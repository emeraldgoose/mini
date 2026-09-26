import time
import threading
from typing import Optional
from dataclasses import dataclass

class Node:
    """
        A node in a doubly linked list, used for implementing LRU (Least Recently Used) cache eviction.
    """
    def __init__(self, key: str, item: Optional['Item'] = None):
        self.key = key
        self.item = item
        self.prev: Optional['Node'] = None
        self.next: Optional['Node'] = None

class DoublyLinkedList:
    """
        A simple doubly linked list to maintain the order of keys for LRU eviction.
    """
    def __init__(self):
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None

    def append(self, node: Node):
        if not self.head:
            self.head = self.tail = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node

    def remove(self, node: Node):
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next
        
        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

    def pop_left(self) -> Optional[Node]:
        if not self.head:
            return None
        
        old_head = self.head
        self.remove(old_head)
        return old_head

@dataclass
class Item:
    value: bytes
    flags: int
    expires_at: Optional[float] = None

    def expired(self) -> bool:
        if self.expires_at is None:
            return False
        
        return time.time() >= self.expires_at

class Store:
    """
        A simple in-memory key-value store that supports setting, getting, 
        and deleting items with optional expiration times (TTL).
    """
    def __init__(self, max_items: int = 100):
        self.data = {}
        self.lock = threading.Lock()  # To ensure thread safety
        self.max_items = max_items
        self.lru_list = DoublyLinkedList()  # For LRU eviction
    
    def set(self, key: str, value: bytes, flags: int = 0, ttl: int = 0):
        expires_at = time.time() + ttl if ttl > 0 else None
        
        item = Item(
            value=value, 
            flags=flags, 
            expires_at=expires_at
        )

        with self.lock:
            # Check if the key already exists and remove it from the LRU list if it does
            old_node = self.data.get(key)

            if old_node:
                self.lru_list.remove(old_node)

            node = Node(key=key, item=item)
            self.data[key] = node
            self.lru_list.append(node)

            # Evict items if we exceed the maximum allowed items
            while len(self.data) > self.max_items:
                lru_node = self.lru_list.pop_left()
                if lru_node:
                    del self.data[lru_node.key]

    def get(self, key: str):
        with self.lock:
            node = self.data.get(key)

            if node is None:
                return None

            if node.item.expired():
                self._remove(node)
                return None

            self._touch(node)
            
            return node.item

    def delete(self, key: str):
        with self.lock:
            node = self.data.get(key)
            
            if node is None:
                return False

            self._remove(node)
            return True

    def _touch(self, node: Node):
        self.lru_list.remove(node)
        self.lru_list.append(node)

    def _remove(self, node: Node):
        del self.data[node.key]
        self.lru_list.remove(node)
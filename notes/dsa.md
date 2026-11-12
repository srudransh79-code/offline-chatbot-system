# Linked List

A linked list is a linear structure where each element, called a node,
holds data and a pointer to the next node. Unlike an array, its elements
are not stored in contiguous memory, so inserting or deleting in the
middle takes O(1) once you are at that position — but finding an element
by index takes O(n), because you must walk from the head node by node.
A singly linked list points only forward; a doubly linked list also
points backward, so you can traverse it in both directions.

# Queue

A queue is a First-In-First-Out (FIFO) structure. Enqueue adds an element
at the rear, dequeue removes an element from the front. Enqueue and
dequeue are both O(1). Example uses: print jobs waiting in order,
processes waiting for the CPU, and breadth-first search, which explores
nodes level by level using a queue.

# Stack

A stack is a Last-In-First-Out (LIFO) structure. Push adds to the top, pop
removes from the top, peek looks at the top without removing it.
Push, pop and peek are all O(1). Example use: undo in an editor, checking
balanced brackets, and function call frames.

# Binary Search Tree (BST)

A binary search tree stores keys so that for every node, all keys in its left
subtree are smaller and all keys in its right subtree are larger.
Search, insert and delete take O(h) time, where h is the height of the tree.
In the worst case (a sorted insertion order) h = n, so operations become O(n).
In a balanced tree h = log n. Inorder traversal of a BST visits keys in
sorted order.

# Tree Traversals

Preorder traversal visits: node, then left subtree, then right subtree.
Inorder traversal visits: left subtree, then node, then right subtree.
Postorder traversal visits: left subtree, then right subtree, then node.
For a binary search tree, inorder gives the keys in ascending order.

# Heap

A heap is a complete binary tree. In a max-heap, every parent is greater than
or equal to its children, so the maximum element is always at the root.
Insert and extract-max take O(log n), peek at the maximum takes O(1).
Heaps are used for priority queues and heap sort.

# Hash Table

A hash table maps keys to buckets using a hash function. With a good hash
function, put, get and remove take O(1) on average. Collisions (two keys
hashing to the same bucket) are handled by chaining: each bucket holds a
linked list of entries, or by open addressing: probing for another free slot.

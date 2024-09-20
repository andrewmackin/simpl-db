import pickle
import os
from node_manager import NodeManager

class BTreeNode:
    def __init__(self, t, leaf=True, node_id=None):
        self.t = t  # Minimum degree
        self.leaf = leaf
        self.keys = []  # List of keys
        self.children = []  # List of child nodes
        self.node_id = node_id # Unique identifier for disk storage

    def insert_non_full(self, key, value, btree):
        i = len(self.keys) - 1
        if self.leaf:
            # Check for existing key and update
            for idx, (k, _) in enumerate(self.keys):
                if k == key:
                    self.keys[idx] = (key, value)
                    btree.node_manager.update_node(self)
                    return
            self.keys.append((key, value))
            self.keys.sort(key=lambda x: x[0])
            btree.node_manager.update_node(self)
        else:
            # Find child to insert into
            while i >= 0 and key < self.keys[i][0]:
                i -= 1
            i += 1
            child_id = self.children[i]
            child = btree.node_manager.load_node(child_id)
            if len(child.keys) == (2 * btree.t) - 1:
                self.split_child(i, btree)
                if key > self.keys[i][0]:
                    i += 1
                child_id = self.children[i]
                child = btree.node_manager.load_node(child_id)
            child.insert_non_full(key, value, btree)

    def split_child(self, i, btree):
        t = btree.t
        y = btree.node_manager.load_node(self.children[i])
        z = BTreeNode(t, y.leaf)
        # Transfer the last t-1 keys from y to z
        z.keys = y.keys[t:]
        y.keys = y.keys[:t - 1]
        if not y.leaf:
            z.children = y.children[t:]
            y.children = y.children[:t]
        # Save the split nodes
        z_id = btree.node_manager.save_node(z)
        y_id = y.node_id
        # Insert new child into self.children
        self.children.insert(i + 1, z_id)
        # Move the median key up to the parent
        self.keys.insert(i, y.keys.pop(-1))
        # Save the parent node
        btree.node_manager.update_node(self)

    def delete_key(self, key):
        # TODO: Implement B-Tree Deletion Alg
        pass

    def traverse(self, btree, results=None):
        if results is None:
            results = []
        for i in range(len(self.keys)):
            if not self.leaf:
                child = btree.node_manager.load_node(self.children[i])
                child.traverse(btree, results)
            results.append(self.keys[i])
        if not self.leaf:
            child = btree.node_manager.load_node(self.children[-1])
            child.traverse(btree, results)
        return results

    def search(self, k, btree):
        i = 0
        while i < len(self.keys) and k > self.keys[i][0]:
            i += 1
        if i < len(self.keys) and self.keys[i][0] == k:
            return self.keys[i][1]
        if self.leaf:
            return None
        child = btree.node_manager.load_node(self.children[i])
        return child.search(k, btree)

class BTree:
    def __init__(self, t=3, storage_path='data/btree'):
        self.t = t
        self.node_manager = NodeManager(storage_path)
        self.storage_path = storage_path
        self.metadata_file = os.path.join(self.storage_path, 'metadata.pkl')

        os.makedirs(self.storage_path, exist_ok=True)

        # Load or initialize metadata
        if os.path.exists(self.metadata_file):
            # Load existing root_id
            with open(self.metadata_file, 'rb') as f:
                metadata = pickle.load(f)
                self.root_id = metadata['root_id']
        else:
            # Initialize new root node
            root = BTreeNode(self.t, leaf=True)
            self.root_id = self.node_manager.save_node(root)
            self._save_metadata()

    def _save_metadata(self):
        with open(self.metadata_file, 'wb') as f:
            pickle.dump({'root_id': self.root_id}, f)

    def insert(self, key, value):
        root = self.node_manager.load_node(self.root_id)
        if len(root.keys) == (2 * self.t) - 1:
            # Root is full, need to split
            new_root = BTreeNode(self.t, leaf=False)
            new_root.children.append(root.node_id)
            new_root.split_child(0, self)
            self.root_id = new_root.node_id
            self.node_manager.update_node(new_root)
            self._save_metadata()  # Save updated root_id
            new_root.insert_non_full(key, value, self)
        else:
            root.insert_non_full(key, value, self)

    def traverse(self):
        root = self.node_manager.load_node(self.root_id)
        return root.traverse(self)

    def search(self, key):
        root = self.node_manager.load_node(self.root_id)
        return root.search(key, self)

    def delete(self, key):
        root = self.node_manager.load_node(self.root_id)
        self._delete_recursive(root, key)
        # Save the root node
        self.node_manager.update_node(root)

    def _delete_recursive(self, node, key):
        for i, (k, _) in enumerate(node.keys):
            if k == key:
                node.keys.pop(i)
                self.node_manager.update_node(node)
                return True
        if node.leaf:
            return False
        else:
            # Search in child nodes
            for child_id in node.children:
                child_node = self.node_manager.load_node(child_id)
                if self._delete_recursive(child_node, key):
                    return True
            return False

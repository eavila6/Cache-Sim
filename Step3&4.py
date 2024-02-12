"""
Author: Carter Young
Date: 2/10/2024
"""
from Step2 import calculate_amat


class BaseCache:
    def __init__(self, cache_size, block_size, set_assoc):
        # Define all requisite parameters
        self.cache_size = cache_size
        self.block_size = block_size
        self.set_assoc = set_assoc
        self.num_sets = self.cache_size // (self.block_size * self.set_assoc)
        self.cache = self.initialize_cache()
        
    def initialize_cache(self):
        # Init cache based on size, block size, set_assoc
        cache = []
        for _ in range(self.num_sets):
            sets = [{'valid': False, 'tag': None, 'LRU': 0, 'dirty': False} for _ in range(self.set_assoc)]
            cache.append(sets)
        return cache
    
    def update_LRU(self, set_index, accessed_block):
        # Increment LRU for all blocks
        for block in self.cache[set_index]:
            block['LRU'] += 1
        accessed_block['LRU'] = 0  # Reset LRU for accessed block

    def get_set_index_and_tag(self, address):
        address_int = int(address, 16)
        index = (address_int // self.block_size) % self.num_sets
        tag = address_int // (self.block_size * self.num_sets)
        return index, tag


class WriteBackCache(BaseCache):
    def __init__(self, cache_size, block_size, set_assoc):
        super().__init__(cache_size, block_size, set_assoc)
        self.write_backs = 0
        self.hits = 0
        self.misses = 0

    def access_cache(self, operation, address):
        set_index, tag = self.get_set_index_and_tag(address)
        if operation == 0:  # Data read
            self.read_data(set_index, tag)
        elif operation == 1:  # Data write
            self.write_data(set_index, tag)

    def read_data(self, set_index, tag):
        cache_set = self.cache[set_index]
        for block in cache_set:
            if block['valid'] and block['tag'] == tag:
                self.update_LRU(set_index, block)
                return True  # If hit
        self.load_block_to_cache(set_index, tag, is_write=False)
        return False  # If miss

    def write_data(self, set_index, tag):
        cache_set = self.cache[set_index]
        for block in cache_set:
            if block['valid'] and block['tag'] == tag:
                block['dirty'] = True  # Mark block as dirty
                self.update_LRU(set_index, block)
                self.hits += 1
                return True  # Hit
        if self.load_block_to_cache(set_index, tag, is_write=True):
            self.hits += 1
        else:
            self.misses += 1
        return False  # Miss

    def load_block_to_cache(self, set_index, tag, is_write):
        lru_block = min(self.cache[set_index], key=lambda x: x['LRU'])
        if lru_block['valid'] and lru_block['dirty']:
            self.write_back(lru_block)
            self.misses += 1
        else:
            pass
        lru_block.update({'valid': True, 'tag': tag, 'LRU': 0, 'dirty': is_write})
        return not lru_block['dirty']

    def write_back(self, block):
        # Simulate writing block back to main mem
        block['dirty'] = False
        self.write_backs += 1  # Increment when we wb


def process_trace_with_write_back(file_path, cache_size=1024, block_size=32):
    assoc = [1, 2, 4, 8, 16, 32]
    H = 1  # Hit time in cycles
    M = 100  # Miss penalty in cycles

    for assoc in assoc:
        # Init instruction and data caches
        instruction_cache = WriteBackCache(cache_size, block_size, assoc)
        data_cache = WriteBackCache(cache_size, block_size, assoc)
        total_accesses = 0

        with open(file_path, 'r') as file:
            for line in file:
                operation, address = line.strip().split()
                operation = int(operation)
                if operation == 2:  # Instruction read
                    instruction_cache.access_cache(operation, address)
                elif operation in (0, 1):  # Data r/w
                    data_cache.access_cache(operation, address)
                total_accesses += 1

        # Calc and print stats for each cache
        instruction_amat = calculate_amat(instruction_cache, H, M)
        data_amat = calculate_amat(data_cache, H, M)
        print(f"Set Associativity {assoc}: Instruction Cache AMAT = {instruction_amat}, Data Cache AMAT = {data_amat}, Write Backs = {instruction_cache.write_backs + data_cache.write_backs}")


file_path = "traces/cc.trace"
process_trace_with_write_back(file_path)

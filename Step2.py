"""
Author: Carter Young
Date: 02/09/2024

This code implements or establishes:
1. Total size in bytes - total size of cache
2. Block size in bytes - size of each block within the cache
3. Set Associativity (Blocks per Set) - how many blocks are in the set
4. Write-Through Mechanism - every write op updates both the cache and main memory immediately
5. LRU - used to replace LRU block within a set with a new block
6. R/W operation -
a
"""


class WriteThroughCache:
    def __init__(self, cache_size, block_size, set_assoc):
        # Define all requisite parameters
        self.cache_size = cache_size
        self.block_size = block_size
        self.set_assoc = set_assoc
        self.num_sets = self.cache_size // (self.block_size * self.set_assoc)
        self.cache = self.initialize_cache()
        self.hits = 0
        self.misses = 0

    def initialize_cache(self):
        # Init cache based on size, block size, set_assoc
        cache = []
        for _ in range(self.num_sets):
            sets = [{'valid': False, 'tag': None, 'LRU': 0} for _ in range(self.set_assoc)]
            cache.append(sets)
        return cache

    def access_cache(self, operation, address):
        # Determine set index and tag from address
        set_index, tag = self.get_set_index_and_tag(address)
        # Perform r/w based on type
        if operation == 0 or operation == 2:  # Data read
            self.read_data(set_index, tag)
        elif operation == 1:  # Data write
            self.write_data(set_index, tag)
        # Instruction read ignored!

    def read_data(self, set_index, tag):
        cache_set = self.cache[set_index]
        for block in cache_set:
            if block['valid'] and block['tag'] == tag:
                self.hits += 1
                self.update_LRU(set_index, block)
                return
        self.misses += 1
        self.load_block_to_cache(set_index, tag)

    def write_data(self, set_index, tag):
        self.load_block_to_cache(set_index, tag, write=True)

    def load_block_to_cache(self, set_index, tag, write=False):
        # Find LRU or invalid blocks
        lru_block = min(self.cache[set_index], key=lambda x: x['LRU'] if x['valid'] else float('-inf'))
        if not lru_block['valid'] or write:
            lru_block['valid'] = True
            lru_block['tag'] = tag
            self.update_LRU(set_index, lru_block)
        self.misses += 1

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

    def report_cache_performance(self):
        print(f"Cache Hits: {self.hits}, Cache Misses: {self.misses}")


def process_trace(file_path, instruction_cache, data_cache):
    with open(file_path, 'r') as file:
        for line in file:
            operation, address = line.strip(). split()
            operation = int(operation)
            if operation == 2:  # Instruction read
                instruction_cache.access_cache(operation, address)
            elif operation in (0, 1):  # Data read or write
                data_cache.access_cache(operation, address)


def simulate_caches(file_path, cache_size=1024, block_size=32, H=1, M=100):
    assoc = [1, 2, 4, 8, 16, 32]
    for assoc in assoc:
        # Init caches
        instruction_cache = WriteThroughCache(cache_size, block_size, assoc)
        data_cache = WriteThroughCache(cache_size, block_size, assoc)

        # Process
        process_trace(file_path, instruction_cache, data_cache)

        # Calc AMAT
        instruction_amat = calculate_amat(instruction_cache, H, M)
        data_amat = calculate_amat(data_cache, H, M)

        print(f"Set Associativity {assoc}:")
        print(f"  Instruction Cache AMAT: {instruction_amat} cycles")
        print(f"  Data Cache AMAT: {data_amat} cycles")

        # Report cache performance
        print("  Instruction Cache Performance:")
        instruction_cache.report_cache_performance()
        print("  Data Cache Performance:")
        data_cache.report_cache_performance()
        print('\n')


def calculate_amat(cache, H, M):
    miss_rate = cache.misses / (cache.hits + cache.misses) if (cache.hits + cache.misses) > 0 else 0
    return H + (miss_rate * M)


file_path = "traces/cc.trace"
simulate_caches(file_path)

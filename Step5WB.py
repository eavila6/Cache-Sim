import csv
"""
Authors: EAVI, Carter Young

Incorporate the L2 cache and write output to a new file step5Results

"""

class WriteBackCache:
    def __init__(self, total_size_bytes, block_size_bytes, blocks_per_set):
        # Constructor for the WriteThroughCache class that initializes the cache with the given size,
        # block size, and blocks per set. Also calculates the number of sets and initializes the cache data structure.
        self.total_size_bytes = total_size_bytes
        self.block_size_bytes = block_size_bytes
        self.blocks_per_set = blocks_per_set
        self.sets = total_size_bytes // (block_size_bytes * blocks_per_set)
        self.cache = self._create_cache()
        self.access_sequence = 0  # To manage LRU policy

    def _create_cache(self):
        # Initialize cache with sets, each containing blocks with a valid bit, dirty bit, tag, and LRU counter
        return [[{'valid': False, 'dirty': False, 'tag': None, 'lru_counter': 0} for _ in range(self.blocks_per_set)] for _ in range(self.sets)]

    def _get_set_and_tag(self, address):
        # Computes set index and tag based on the given memory address
        set_index = (address // self.block_size_bytes) % self.sets
        tag = address // (self.block_size_bytes * self.sets)
        return set_index, tag

    def read(self, address):
        # Updates LRU counter on hit, calls load_block to fetch and load block if miss
        set_index, tag = self._get_set_and_tag(address)
        for block in self.cache[set_index]:
            if block['valid'] and block['tag'] == tag:
                # Update LRU counter on hit
                block['lru_counter'] = self.access_sequence
                self.access_sequence += 1
                return True  # Read hit
        # Read miss: Load the block into the cache
        self.load_block(set_index, tag)
        return False

    def write(self, address):
        # Writes through to main. Updates LRU if block is in cache. Else, load into cache.
        set_index, tag = self._get_set_and_tag(address)
        for block in self.cache[set_index]:
            if block['tag'] == tag:
                # Update the block as dirty and LRU counter on hit
                block['dirty'] = True
                block['lru_counter'] = self.access_sequence
                self.access_sequence += 1
                return True  # Write hit
        # Write miss: Load the block into the cache, mark as dirty
        self.load_block(set_index, tag, dirty=True)
        return False

    def load_block(self, set_index, tag, dirty=False):
        # Finds the LRU block to replace
        lru_block = min(self.cache[set_index], key=lambda x: x['lru_counter'])
        # If the LRU block is dirty, write it back to main memory
        if lru_block['valid'] and lru_block['dirty']:
            self.write_back(lru_block)
        # Load the new block
        lru_block['valid'] = True
        lru_block['dirty'] = dirty
        lru_block['tag'] = tag
        lru_block['lru_counter'] = self.access_sequence

    def write_back(self, block):
        # Simulate writing the block back to main memory
        # Actual write-back logic to main memory would go here
        block['dirty'] = False


def WBCacheSimulation(trace_name):
    """ Sims cache given associativity for the passed traces.
        Processes each mem access in trace, calcs hits/misses, hit rates, AMAT.
    """
    associativities = [1, 2, 4, 8, 16, 32]
    total_size_bytes = 1024
    block_size_bytes = 32
    hit_time = 1  # H
    miss_penalty = 100  # M
    csv_filename = f"WBResults/{trace_name}_wb.csv"

    trace_lines = read_trace_file(f"traces/{trace_name}.trace")

    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['Assoc.', 'L1I accesses', 'L1I misses', 'L1D accesses', 'L1D misses', 'L2 accesses', 'L2 misses', 'L1I hit rate',
                          'L1D hit rate', 'L2 hit rate','L1I AMAT', 'L1D AMAT', 'L2 AMAT']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for assoc in associativities:
            i_cache = WriteBackCache(total_size_bytes, block_size_bytes, 2)
            d_cache = WriteBackCache(total_size_bytes, block_size_bytes, 2)
            l2Cache = WriteBackCache(16384, 128, assoc)

            i_hits, i_misses, d_hits, d_misses, thit, tmiss = 0, 0, 0, 0, 0, 0

            for reference_type, address in trace_lines:
                if reference_type == 2:  # Instruction read
                    if i_cache.read(address):
                        i_hits += 1
                    else:
                        i_misses += 1

                        # first, check L2 cache if instruction is there
                        # if instruction is in L2 cache, load into i_cache
                        # if not, store instruction to L2 cache
                        if l2Cache.read(address):
                            thit += 1
                            i_cache.write(address)
                        else:
                            l2Cache.write(address)
                            tmiss += 1

                else:  # Data read/write
                    if d_cache.write(address) if reference_type == 1 else d_cache.read(address):
                        d_hits += 1
                    else:
                        d_misses += 1

                        # same as the i_cache process
                        # first, check L2 cache if data is there
                        # if instruction is in L2 cache, load into d_cache
                        # if not, store data to L2 cache
                        if l2Cache.read(address):
                            thit += 1
                            d_cache.write(address)
                        else:
                            l2Cache.write(address)
                            tmiss += 1

            i_miss_rate = i_misses / (i_hits + i_misses) if (i_hits + i_misses) else 0
            d_miss_rate = d_misses / (d_hits + d_misses) if (d_hits + d_misses) else 0
            l2MissRate = tmiss / (thit + tmiss) if (thit + tmiss) > 0 else 0  # calculating miss rate for l2 cache

            l2HitRate = 1 - l2MissRate

            i_amat = hit_time + (i_miss_rate * miss_penalty)
            d_amat = hit_time + (d_miss_rate * miss_penalty)
            amat = hit_time + ((i_miss_rate + d_miss_rate) / 2) * (10 + l2MissRate * miss_penalty)

            writer.writerow({
                'Assoc.': assoc,
                'L1I accesses': i_hits,
                'L1I misses': i_misses,
                'L1D accesses': d_hits,
                'L1D misses': d_misses,
                'L2 accesses': thit,
                'L2 misses': tmiss,
                'L1I hit rate': f"{i_hits / (i_hits + i_misses) if (i_hits + i_misses) else 0:.4f}",
                'L1D hit rate': f"{d_hits / (d_hits + d_misses) if (d_hits + d_misses) else 0:.4f}",
                'L2 hit rate': f"{l2HitRate: .4f}",
                'L1I AMAT': f"{i_amat:.2f}",
                'L1D AMAT': f"{d_amat:.2f}",
                'L2 AMAT': f"{amat:.2f}"
            })

    print(f"Results have been written to {csv_filename}")
    return csv_filename


def read_trace_file(file_path):
    """
    Reads a trace file and returns a list of (reference_type, address) tuples.

    Args:
    - file_path: Path to the trace file

    Returns:
    - A list of tuples, where each tuple contains:
        - reference_type (int): The type of memory reference (0 for data read, 1 for data write, 2 for instruction read)
        - address (int): The memory address accessed, as an integer
    """
    trace_lines = []
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) == 2:
                reference_type, address_hex = parts
                reference_type = int(reference_type)
                address = int(address_hex, 16)  # Convert hex address to integer
                trace_lines.append((reference_type, address))
    return trace_lines


filename = 'spice'  # Write 'cc', 'spice', or 'tex' here to change trace
trace_lines = read_trace_file(f"traces/{filename}.trace")
WBCacheSimulation(filename)
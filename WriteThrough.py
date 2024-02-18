"""
Author: Carter Young
Date: 02/09/2024 - 02/17/2024

This code represents an implementation of steps 1 & 2 for CS
429, Project 1 (Flores, 2024).
"""
import csv


class WriteThroughCache:
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
        # Initializes cache with sets, each containing blocks with a valid bit, tag, and LRU counter
        return [[{'valid': False, 'tag': None, 'lru_counter': 0} for _ in range(self.blocks_per_set)] for _ in range(self.sets)]

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
                block['lru_counter'] = self.access_sequence
                self.access_sequence += 1
                return True  # Hit
        # Miss: Load the block into the cache
        self.load_block(set_index, tag)
        return False

    def write(self, address):
        # Writes through to main. Updates LRU if block is in cache. Else, load into cache.
        set_index, tag = self._get_set_and_tag(address)
        block_loaded = False
        for block in self.cache[set_index]:
            if block['tag'] == tag:
                block['lru_counter'] = self.access_sequence
                block_loaded = True
                break
        if not block_loaded:
            self.load_block(set_index, tag)
        # Write-through cache: Assume write to main memory here
        self.access_sequence += 1
        return False  # Always count as a miss for write

    def load_block(self, set_index, tag):
        # Finds the LRU block to replace
        lru_block = min(self.cache[set_index], key=lambda x: x['lru_counter'])
        lru_block['valid'] = True
        lru_block['tag'] = tag
        lru_block['lru_counter'] = self.access_sequence


class CacheSimulation:
    def __init__(self, total_size_bytes=1024, block_size_bytes=32, H=1, M=100):
        # Initializes sim with default cache and block size, as well as hit time and miss penalty
        self.total_size_bytes = total_size_bytes
        self.block_size_bytes = block_size_bytes
        self.H = H
        self.M = M

    def simulate_trace(self, associativity, trace_lines):
        """ Sims cache given associativity for the passed traces.
            Processes each mem access in trace, calcs hits/misses, hit rates, AMAT.
        """
        # Create caches
        i_cache = WriteThroughCache(self.total_size_bytes, self.block_size_bytes, associativity)
        d_cache = WriteThroughCache(self.total_size_bytes, self.block_size_bytes, associativity)

        # Track hits and misses
        i_hits, i_misses, d_hits, d_misses = 0, 0, 0, 0

        for line in trace_lines:
            reference_type, address = line  # Directly unpack the tuple

            # Determine cache and action
            if reference_type == 2:  # Instruction read
                if i_cache.read(address):
                    i_hits += 1
                else:
                    i_misses += 1
            else:  # Data read/write
                if reference_type == 1:  # Data write
                    d_cache.write(address)  # Write operation
                    d_misses += 1  # Write is always a miss
                else:  # Data read
                    if d_cache.read(address):
                        d_hits += 1  # If it exists in d-cache, hit
                    else:
                        d_misses += 1  # If it does not exist in d-cache, miss

        # Return hits and misses along with AMAT
        i_miss_rate = i_misses / (i_hits + i_misses) if (i_hits + i_misses) > 0 else 0  # calc miss rate for i-cache
        d_miss_rate = d_misses / (d_hits + d_misses) if (d_hits + d_misses) > 0 else 0  # calc miss rate for d-cache

        # Return hit rate
        i_hit_rate = 1 - i_miss_rate
        d_hit_rate = 1 - d_miss_rate

        i_amat = self.H + (i_miss_rate * self.M)  # calc i-amat according to project desc.
        d_amat = self.H + (d_miss_rate * self.M)  # calc d-amat according to project desc.

        return (i_hits, i_misses, d_hits, d_misses, i_hit_rate, d_hit_rate, i_amat, d_amat)

    def run_simulation(self, trace_name):
        # Run sims and write to CSV
        associativities = [1, 2, 4, 8, 16, 32]
        trace_file_path = f"traces/{trace_name}.trace"
        csv_filename = f"WTResults/{trace_name}_wt.csv"

        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = ['Assoc.', 'L1I accesses', 'L1I misses', 'L1D accesses', 'L1D misses', 'L1I hit rate',
                          'L1D hit rate', 'L1I AMAT', 'L1D AMAT']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for assoc in associativities:
                i_hits, i_misses, d_hits, d_misses, i_hit_rate, d_hit_rate, i_amat, d_amat = self.simulate_trace(assoc, trace_lines)

                writer.writerow({
                    'Assoc.': assoc,
                    'L1I accesses': i_hits,
                    'L1I misses': i_misses,
                    'L1D accesses': d_hits,
                    'L1D misses': d_misses,
                    'L1I hit rate': f"{i_hit_rate:.4f}",
                    'L1D hit rate': f"{d_hit_rate:.4f}",
                    'L1I AMAT': f"{i_amat:.2f}",
                    'L1D AMAT': f"{d_amat:.2f}"
                })

        print(f"Results have been written to {csv_filename}")
        return csv_filename


def read_trace_file(file_path):
    """ Reads a trace file and returns a list of (reference_type, address) tuples. """
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
simulation = CacheSimulation()
csv_file = simulation.run_simulation(filename)

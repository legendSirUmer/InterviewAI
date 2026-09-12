"""
Coding Problems Bank for Coding Interview Mode.
Provides rich problem definitions, starter code templates, examples,
constraints, and evaluation criteria for AI Code Evaluator.
"""

CODING_PROBLEMS = [
    {
        "id": "two_sum",
        "title": "Two Sum",
        "difficulty": "Easy",
        "category": "Data Structures & Algorithms",
        "description": """Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice. You can return the answer in any order.""",
        "examples": [
            "Input: nums = [2,7,11,15], target = 9 -> Output: [0,1] (Because nums[0] + nums[1] == 9)",
            "Input: nums = [3,2,4], target = 6 -> Output: [1,2]",
            "Input: nums = [3,3], target = 6 -> Output: [0,1]",
        ],
        "constraints": [
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9",
            "Only one valid answer exists.",
        ],
        "starter_code": """def two_sum(nums: list[int], target: int) -> list[int]:
    # Write your solution here
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
""",
        "optimal_time": "O(N)",
        "optimal_space": "O(N)",
    },
    {
        "id": "lru_cache",
        "title": "LRU Cache (Least Recently Used)",
        "difficulty": "Medium",
        "category": "System & Data Structures",
        "description": """Design a data structure that follows the constraints of a Least Recently Used (LRU) cache.

Implement the `LRUCache` class:
- `LRUCache(int capacity)`: Initialize the LRU cache with positive size `capacity`.
- `int get(int key)`: Return the value of the `key` if the key exists, otherwise return `-1`.
- `void put(int key, int value)`: Update the value of the `key` if the `key` exists. Otherwise, add the `key-value` pair to the cache. If the number of keys exceeds the `capacity` from this operation, evict the least recently used key.

The functions `get` and `put` must each run in `O(1)` average time complexity.""",
        "examples": [
            "lRUCache = LRUCache(2);\nlRUCache.put(1, 1);\nlRUCache.put(2, 2);\nlRUCache.get(1);    // returns 1\nlRUCache.put(3, 3); // evicts key 2\nlRUCache.get(2);    // returns -1 (not found)",
        ],
        "constraints": [
            "1 <= capacity <= 3000",
            "0 <= key <= 10^4",
            "0 <= value <= 10^5",
            "At most 2 * 10^5 calls will be made to get and put.",
        ],
        "starter_code": """class Node:
    def __init__(self, key=0, val=0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        # Dummy head and tail for O(1) removals
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key: int) -> int:
        # Implement O(1) get
        pass

    def put(self, key: int, value: int) -> None:
        # Implement O(1) put with LRU eviction
        pass
""",
        "optimal_time": "O(1) for both get and put",
        "optimal_space": "O(capacity)",
    },
    {
        "id": "group_anagrams",
        "title": "Group Anagrams",
        "difficulty": "Medium",
        "category": "Hash Maps & Strings",
        "description": """Given an array of strings `strs`, group the anagrams together. You can return the answer in any order.

An Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.""",
        "examples": [
            'Input: strs = ["eat","tea","tan","ate","nat","bat"] -> Output: [["bat"],["nat","tan"],["ate","eat","tea"]]',
            'Input: strs = [""] -> Output: [[""]]',
            'Input: strs = ["a"] -> Output: [["a"]]',
        ],
        "constraints": [
            "1 <= strs.length <= 10^4",
            "0 <= strs[i].length <= 100",
            "strs[i] consists of lowercase English letters.",
        ],
        "starter_code": """from collections import defaultdict

def group_anagrams(strs: list[str]) -> list[list[str]]:
    # Write your solution here
    pass
""",
        "optimal_time": "O(N * K log K) or O(N * K)",
        "optimal_space": "O(N * K)",
    },
    {
        "id": "rate_limiter",
        "title": "Sliding Window Rate Limiter",
        "difficulty": "Hard",
        "category": "Backend System & Concurrency",
        "description": """Implement an in-memory Sliding Window Rate Limiter class `RateLimiter` that enforces an API request rate limit for multiple client IDs.

Requirements:
- `RateLimiter(max_requests: int, window_seconds: int)`: Initializes the rate limiter.
- `allow_request(client_id: str, timestamp_seconds: float) -> bool`: Returns `True` if the client is permitted to make a request at `timestamp_seconds`, or `False` if they exceeded `max_requests` in the preceding `window_seconds`.
- Handles high concurrency cleanly and purges outdated timestamps to prevent memory leaks.""",
        "examples": [
            "limiter = RateLimiter(max_requests=2, window_seconds=10)\nlimiter.allow_request('user_1', 1.0) -> True\nlimiter.allow_request('user_1', 2.0) -> True\nlimiter.allow_request('user_1', 3.0) -> False (limit reached)\nlimiter.allow_request('user_1', 12.0) -> True (window slid forward)",
        ],
        "constraints": [
            "max_requests >= 1",
            "window_seconds >= 1",
            "Timestamps are monotonically increasing per client.",
        ],
        "starter_code": """from collections import deque
import threading

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.client_windows = {}
        self.lock = threading.Lock()

    def allow_request(self, client_id: str, timestamp_seconds: float) -> bool:
        # Implement sliding window log with thread safety
        pass
""",
        "optimal_time": "O(1) amortized per request",
        "optimal_space": "O(clients * max_requests)",
    },
]


def get_all_problems():
    """Returns list of available coding problems."""
    return CODING_PROBLEMS


def get_problem_by_id(problem_id):
    """Retrieves a specific problem by ID."""
    for p in CODING_PROBLEMS:
        if p["id"] == problem_id:
            return p
    return CODING_PROBLEMS[0]

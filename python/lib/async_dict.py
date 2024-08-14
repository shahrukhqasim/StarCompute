import asyncio

class AsyncDict:
    def __init__(self):
        self._dict = {}
        self._condition = asyncio.Condition()

    async def set_item(self, key, value):
        async with self._condition:
            self._dict[key] = value
            self._condition.notify_all()

    async def get_item(self, key):
        async with self._condition:
            while key not in self._dict:
                await self._condition.wait()
            return self._dict[key]

# Example usage
async def producer(async_dict):
    await asyncio.sleep(2)  # Simulate a delay
    await async_dict.set_item("key1", "value1")
    print("Item set!")

async def consumer(async_dict):
    print("Waiting for item...")
    value = await async_dict.get_item("key1")
    print(f"Got item: {value}")

async def main():
    async_dict = AsyncDict()
    await asyncio.gather(producer(async_dict), consumer(async_dict))


if __name__ == "__main__":
    asyncio.run(main())

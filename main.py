from parent_agent.parent_agent import async_main
import asyncio

if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An unhandled error occurred in main: {e}")
        import traceback
        traceback.print_exc()
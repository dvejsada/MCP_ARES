import server
import asyncio

def main():
    """Main entry point for the package."""
    asyncio.run(server.main())

# Optionally expose other important items at package level
__all__ = ['ares_call', 'server']

if __name__ == "__main__":
    main()
# import os

# Specify token path
# parent_dir = os.path.dirname(__file__)
# os.environ["CUBERG_TOKEN_PATH"] = os.path.join(parent_dir, ".cuberg_token")

__version__ = "0.0.1"
__all__ = ["__version__"]

if __name__ == "__main__":
    # Note: needed to get version for Docker build, etc.
    print(__version__)

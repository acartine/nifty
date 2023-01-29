import string
import sys

# why base62?
#
# With a trillion links, we have a short link of len 7 with human
# readable characters
#
# at some point we would want to harvest old links and reuse them
# but this should get us pretty far

# Define the base 62 characters
base62_chars = string.digits + string.ascii_letters


# Define a function to convert a number to base 62
def base62_encode(num: int) -> str:
    base62 = ''
    while num > 0:
        num, remainder = divmod(num, 62)
        base62 = base62_chars[remainder] + base62
    return base62


# Define a function to convert a base 62 string to a number
def base62_decode(base62: str) -> int:
    num = 0
    for char in base62:
        num = num * 62 + base62_chars.index(char)
    return num


if __name__ == "__main__":
    args = sys.argv[1:]
    print(f"{base62_encode(int(args[0]))}")

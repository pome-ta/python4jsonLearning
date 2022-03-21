import sys


s = "a" * 1000

print(len(s))  # 1000
print(sys.getsizeof(s))  # 1049

s2 = "❄" + "a" * 999
print(len(s2))  # 1000
print(sys.getsizeof(s2))  # 2074

s3 = "💵" + "a" * 999
print(len(s3))  # 1000
print(sys.getsizeof(s3))  # 4076

s4 = "あ" + "a" * 999
print(len(s4))  # 1000
print(sys.getsizeof(s4))  # 2074

s5 = "🙇‍♂️" + "a" * 999
print(len(s5))  # 1003
print(sys.getsizeof(s5))  # 4088

s6 = "🙇‍" + "a" * 999
print(len(s6))  # 1001
print(sys.getsizeof(s6))  # 4080


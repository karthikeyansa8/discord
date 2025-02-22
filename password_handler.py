import random
import string

def password_generator():
    password = ''.join(random.choices(string.digits, k=4)) + '1234'
    return password

if __name__ == '__main__':
    password = password_generator()
    
    print(password)
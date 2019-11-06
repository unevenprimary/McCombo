prefs = [694, 699]
seed = 7777777

def generate(digits=7, prefs=prefs, seed=seed):
    m = int('1' + '0'*digits)
    a = 28637181
    c = 7777171
    with open('numbers.txt', 'w+') as outfile:
        for prefix in prefs:
            print(f'Now generating numbers with prefix {prefix}...')
            num = seed
            for _ in range(m):
                num = (num*a + c) % m
                s = f'{prefix:0>3d}{num:0>7d}\n'
                outfile.write(s)
    print('Finished generating numbers! Press <ENTER>')
    input('')


if __name__ == '__main__':
    generate()

import sys

in_filename = sys.argv[1]
out_filename = sys.argv[2]

in_f = open(in_filename, 'r')
lines = in_f.readlines()
in_f.close()
out_f = open(out_filename, 'w')
for l in lines:
    if len(l) == 21:
        out_f.write(l)
out_f.close()

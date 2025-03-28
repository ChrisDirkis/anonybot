with open("in.txt") as f:
    lines = f.readlines()
    def process_line(line):
        words = line.strip().split(", ")
        return "  •  ".join([w[0].upper() + w[1:] for w in words])
    lines = [process_line(line) for line in lines if len(line) > 5]
    print("\n".join(lines))
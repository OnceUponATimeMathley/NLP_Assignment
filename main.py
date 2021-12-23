from models.parser import process
import sys

def main():
    if len(sys.argv) < 2:
        raise Exception("Usage: python main.py <input file name>")
    input_file_path = "../Assignment/Input/"
    input_file_name = sys.argv[1]

    with open(input_file_path + input_file_name, 'r') as input_file:
        questions = input_file.read().splitlines()

    open("../Assignment/Output/output_a.txt", 'w').close()
    open("../Assignment/Output/output_b.txt", 'w').close()
    open("../Assignment/Output/output_c.txt", 'w').close()
    open("../Assignment/Output/output_d.txt", 'w').close()
    open("../Assignment/Output/output_e.txt", 'w').close()
    open("../Assignment/Output/output_f.txt", 'w').close()

    print("Start processing!")
    for ques in questions:
        print(ques)
        process(ques)

    print("Process completed! Please see Output folder for the result")

if __name__ == "__main__":
    main()
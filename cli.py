from gams2pyomo import GAMSTranslator
from sys import argv
import argparse

def main():
    args = argparse.ArgumentParser(
            prog='GAMSTranslator cli'
    )
    args.add_argument('inputfile')
    args.add_argument('-o', '--outputfile', required=False)
    args = args.parse_args()
    fp = args.inputfile
    if args.outputfile is None:
        args.outputfile = args.inputfile.replace(".gms", ".py")

    gp = GAMSTranslator(fp)
    res = gp.translate()


    with open(args.outputfile, 'w') as f:
        f.write(res)
    
    print("Success")



if __name__ == "__main__":
    main()

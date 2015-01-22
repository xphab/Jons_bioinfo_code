#!/usr/bin/env python

from __future__ import division

__author__ = "Jonathan Leff"
__email__ = "jonathan.leff@colorado.edu"
__version__ = "0.0.1"

import sys
import os
from os.path import split, splitext
from time import gmtime, strftime
# from Bio import SeqIO
# from Bio.Seq import Seq
from itertools import izip
import gzip
import argparse


parser = argparse.ArgumentParser(description=
	"Demultiplex Illumina sequences based on fusion barcodes and stores sequences for individual files in separate files. NOTE: demultiplexing is based on order of sequences in the index and read files and DOES NOT check headers.")
parser.add_argument('-i','--sequence_reads_fp', required=True,\
    help='The sequence reads in fastq format')
parser.add_argument('-r','--reverse_reads_fp', required=True,\
    help='The reverse sequence reads in fastq format')
parser.add_argument('-b','--barcode_reads_fp', required=True,\
    help='The index (barcode) reads in fastq format')
parser.add_argument('-m','--mapping_file_fp', required=True,\
    help='The the mapping file with barcodes as second column in txt format')
parser.add_argument('-o','--output_dir',\
	help='The output directory')
parser.add_argument('-c','--rev_comp_mapping_barcodes',action='store_true',\
   	    help='should the mapping file barcodes be reverse complemented?',default=False)


def main():
	args = parser.parse_args()

	sequence_reads_fp = args.sequence_reads_fp
	reverse_reads_fp = args.reverse_reads_fp
	output_dir = args.output_dir
	barcode_reads_fp = args.barcode_reads_fp
	mapping_fp = args.mapping_file_fp
	rc = args.rev_comp_mapping_barcodes


	if sequence_reads_fp.endswith('.gz'):
		seqs = gzip.open(sequence_reads_fp,'rb')
	else:
		seqs = open(sequence_reads_fp,'U')
	if reverse_reads_fp.endswith('.gz'):
		revSeqs = gzip.open(reverse_reads_fp,'rb')
	else:
		revSeqs = open(reverse_reads_fp,'U')
	if barcode_reads_fp.endswith('.gz'):
		barcodes = gzip.open(barcode_reads_fp,'rb')
	else:
		barcodes = open(barcode_reads_fp,'U')
	mapping = open(mapping_fp,'U')
	if not output_dir:
		input_file_basename, input_file_ext = \
		 splitext(split(sequence_reads_fp)[1])
		output_dir = '%s_demultiplexed' % (input_file_basename)
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	else:
		print "Output directory already exists. Delete and try again."
		exit()

	time = str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
	sys.stdout.write('Start time: '+time+'\n')

	# create dictionary with sample IDs and barcodes
	barcodeDict = {}
	for line in mapping:
		if list(line)[0] == '#':
			continue
		sampleID = line.strip().split('\t')[0]
		barcode = line.strip().split('\t')[1]
		if rc:
			barcode = reverse_complement(barcode)
		barcodeDict[barcode] = sampleID
		# print barcode

	# export sequences to files with sample IDs as filenames
	number_seqs = 0
	number_matched = 0
	printcounter = 0
	for i, ((hFwd, seqFwd, qualFwd), (hbc, bc, bcQual), (hRev, seqRev, qualRev)) in enumerate(izip(basic_fastq_parser(seqs), basic_fastq_parser(barcodes), basic_fastq_parser(revSeqs))):
		# print hbc, bc, bcQual
		# print bc
		# print bcQual
		if len(bc) == 13:
			bc = bc[:12]
		if bc in barcodeDict:
			number_matched += 1
			sampleID = barcodeDict[bc]
			fpFwd = output_dir + "/" + sampleID + "_1.fq"
			with open(fpFwd, 'a') as handle1:
				write_fastq(hFwd, seqFwd, qualFwd, handle1)
			fpRev = output_dir + "/" + sampleID + "_2.fq"
			with open(fpRev, 'a') as handle2:
				write_fastq(hRev, seqRev, qualRev, handle2)
			if(printcounter == 1000):
				pct_kept = number_matched / number_seqs * 100
				sys.stdout.write('\r')
				sys.stdout.write('Seqs processed: %d Percent kept: %5.1f%%' % (number_seqs,pct_kept))
				sys.stdout.flush()
				printcounter = 0
			printcounter += 1
		else:
			if(printcounter == 1000):
				pct_kept = number_matched / number_seqs * 100
				sys.stdout.write('\r')
				sys.stdout.write('Seqs processed: %d Percent kept: %5.1f%%' % (number_seqs,pct_kept))
				sys.stdout.flush()
				printcounter = 0
			printcounter += 1
		number_seqs += 1

	pct_kept = number_matched / number_seqs * 100
	sys.stdout.write('\r')
	sys.stdout.write('Seqs processed: %d Percent kept: %5.1f%%' % (number_seqs,pct_kept))
	sys.stdout.flush()
				
	time = str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
	sys.stdout.write('\n'+'End time: '+time+'\n')


def basic_fastq_parser(in_f):
	lineno, head, seq, qual = 0, "", "", ""
	for l in in_f:
		lineno += 1
		# print "line:" + str(lineno)
		# print l.strip()
		# print "modulo" + str(lineno%4)
		if lineno%4 == 1: head = l.strip()
		elif lineno%4 == 2: seq = l.strip()
		elif lineno%4 == 0:
			qual = l.strip()
			yield head, seq, qual


def write_fastq(header, seq, qual, out_f):
	# out_f.write('apple%spear' % (' brown '))
	out_f.write('%s\n%s\n+\n%s' % (header, seq, qual))

reverse_complement = lambda x: ''.join([{'A':'T','C':'G','G':'C','T':'A'}[B] for B in x][::-1])


if __name__ == "__main__":
    main()
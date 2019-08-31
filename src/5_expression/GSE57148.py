#!/usr/bin/env python3
"""
Generate GSE57148
"""

__author__ = "Enrico Maiorino"
__version__ = "0.1.0"
__license__ = "MIT"

import logging
import GEOparse
import argparse
import pandas as pd
from funcs import utils
from os.path import join
import shutil
import urllib.request as request
from contextlib import closing
import numpy as np


def main(args):
    logging.basicConfig(level=logging.INFO,
                        format='%(module)s:%(levelname)s:%(asctime)s:%(message)s',
                            handlers=[logging.FileHandler("../logs/report.log")])
    logging.info(args)

    utils.create_dir_if_not_exist(args.out_expr_dir)
    utils.create_dir_if_not_exist(join(args.out_expr_dir,'raw'))
    utils.create_dir_if_not_exist(join(args.out_expr_dir,'processed'))

    gse = GEOparse.get_GEO(geo='GSE57148', destdir=join(args.out_expr_dir,'raw'))
    with closing(request.urlopen(
            'ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE57nnn/GSE57148/suppl/GSE57148_COPD_FPKM_Normalized.txt.gz')) as r:
        with open(join(args.out_expr_dir,'raw','GSE57148_COPD_FPKM_Normalized.txt.gz'), 'wb') as f:
            shutil.copyfileobj(r, f)
    counts = pd.read_csv(join(args.out_expr_dir,'raw','GSE57148_COPD_FPKM_Normalized.txt.gz'),sep='\t')
    annotated2 = counts.rename(columns={gse.gsms[gsm].metadata['title'][0].split(' ')[-1]: gsm for gsm in gse.gsms})
    print(annotated2.isnull().values.any(axis=1).sum())
    print(annotated2.isnull().values.all(axis=1).sum())
    convmatr = utils.gm._sources['biomart'].set_index('symbol')
    annotated2['ENTREZ_GENE_ID'] = convmatr.loc[annotated2.GeneName.tolist()].entrez.tolist()
    print(annotated2.shape)
    annotated2 = annotated2[~annotated2.ENTREZ_GENE_ID.isnull()]
    print(annotated2.shape)
    annotated2['ENTREZ_GENE_ID'] = annotated2['ENTREZ_GENE_ID'].astype(int)
    del annotated2['GeneName']
    annotated2 = annotated2.set_index('ENTREZ_GENE_ID')

    disease_cls = ['disease state: COPD']
    healthy_cls = ['disease state: Normal']
    logging.info(disease_cls)
    logging.info(healthy_cls)
    disease_gsm = [gsm for gsm in gse.gsms if gse.gsms[gsm].metadata['characteristics_ch1'][0] in disease_cls]
    healthy_gsm = [gsm for gsm in gse.gsms if gse.gsms[gsm].metadata['characteristics_ch1'][0] in healthy_cls]
    logging.info("Disease GSM: {}, Healthy GSM: {}".format(len(disease_gsm), len(healthy_gsm)))
    utils.create_dir_if_not_exist(args.out_expr_dir)
    utils.write_expr(join(args.out_expr_dir, 'processed', 'expr.tsv'), annotated2)
    utils.write_text(join(args.out_expr_dir, 'processed', 'disease_gsms.txt'), disease_gsm)
    utils.write_text(join(args.out_expr_dir, 'processed', 'healthy_gsms.txt'), healthy_gsm)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process GSE57148')
    parser.add_argument('out_expr_dir', type=str, help='Output directory for expression data file and GSM lists')
    args = parser.parse_args()
    main(args)
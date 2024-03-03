import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from tools import read_dataset_pickle
from preprocess import preprocess_dataset
from filterdf import filter_in_year

app = Flask(__name__)
CORS(app)

dc1 = read_dataset_pickle(["dataset/DC1"])[0]
dc1 = preprocess_dataset(dc1)

@app.route("/api/demografi", methods=["GET"])
def data_demografi():
    data = {}
    tipe_data = request.args.get("tipe_data")

    if tipe_data is None:
        data["index"] = dc1["kabupaten"].value_counts().index.values.tolist()
        data["values"] = dc1["kabupaten"].value_counts().values.tolist()
        return data
    elif tipe_data == "timeseries":
        temp_df = dc1[["waktu_registrasi", "kabupaten"]]
        temp_df = filter_in_year(temp_df, "waktu_registrasi", 2021)

        # Pick top 10
        temp_df = temp_df[["kabupaten", "waktu_registrasi"]]
        temp_df["kabupaten_filtered"] = temp_df["kabupaten"]
        temp_df.loc[~temp_df["kabupaten_filtered"].isin(temp_df["kabupaten"].value_counts()[:10].index), "kabupaten_filtered"] = "Lainnya"
        temp_df = temp_df.drop(columns="kabupaten")

        temp_df = pd.crosstab(temp_df["waktu_registrasi"], temp_df["kabupaten_filtered"])
        temp_df = temp_df.resample("W").sum()

        data["index"] = temp_df.index.strftime("%Y-%m-%d").tolist()
        data["columns"] = temp_df.columns.tolist()
        data["values"] = temp_df.values.transpose().tolist()
        return data

    return data

@app.route("/api/usia", methods=["GET"])
def data_usia():
    # Menghitung jumlah kategori pada setiap tahun
    dc1_count = dc1.groupby([dc1['waktu_registrasi'].dt.year, 'kategori_usia']).size().unstack(fill_value=0).reset_index()

    # Menghitung jumlah kategori secara keseluruhan
    total_kategori = dc1['kategori_usia'].value_counts().to_dict()

    data = {
        "kategori": total_kategori,
        "bytahun": dict(zip(dc1_count['waktu_registrasi'], dc1_count.set_index('waktu_registrasi').to_dict(orient='index').values()))
    }
    return data

@app.route("/api/jeniskelamin", methods=["GET"])
def data_jeniskelamin():
    data = {}
    data["index"] = dc1["jenis_kelamin"].value_counts().index.values.tolist()
    data["values"] = dc1["jenis_kelamin"].value_counts().values.tolist()
    return data

@app.route("/api/penjamin", methods=["GET"])
def data_jenispenjamin():
    data = {}
    data["index"] = dc1["jenis_penjamin"].value_counts().index.values.tolist()
    data["values"] = dc1["jenis_penjamin"].value_counts().values.tolist()
    return data

@app.route("/api/instansi", methods=["GET"])
def data_instansi():
    # Menghapus data dengan nama_instansi_utama bernama BPJS Kesehatan
    filtered_data = dc1[dc1["nama_instansi_utama"] != "BPJS Kesehatan"]

    # Menghitung ulang value_counts setelah data di-filter
    data = {}
    data["index"] = filtered_data["nama_instansi_utama"].value_counts().index.values.tolist()
    data["values"] = filtered_data["nama_instansi_utama"].value_counts().values.tolist()

    return data

from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import os
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "your_secret_key"
CORS(app)

# ✅ Load Excel Data Function
def load_data(file_name):
    try:
        df = pd.read_excel(file_name, engine="openpyxl")
        df = df.rename(columns=str.lower)
        required_columns = {'name', 'amazon', 'flipkart'}

        if not required_columns.issubset(df.columns):
            print(f"❌ Warning: Missing columns in {file_name}. Found: {df.columns}")
            return pd.DataFrame()

        df['name'] = df['name'].astype(str).str.strip().str.lower()
        print(f"✅ Loaded {file_name} with {len(df)} products.")
        return df
    except Exception as e:
        print(f"❌ Error loading {file_name}: {e}")
        return pd.DataFrame()

# ✅ Load Data for All Categories
mobiles_df = load_data("mobiles.xlsx")
headsets_df = load_data("headsets.xlsx")
speakers_df = load_data("speakers.xlsx")
tablets_df = load_data("tablets.xlsx")
smartwatches_df = load_data("smartwatches.xlsx")

# ✅ Wishlist Data Handling
wishlist_file = "wishlist.xlsx"
def load_wishlist():
    if not os.path.exists(wishlist_file):
        pd.DataFrame(columns=["Category", "Product Name", "Price", "URL"]).to_excel(wishlist_file, index=False)
    return pd.read_excel(wishlist_file, engine="openpyxl")

def add_to_wishlist(category, product_name, price, url):
    wishlist_df = load_wishlist()
    new_entry = pd.DataFrame([{
        "Category": category,
        "Product Name": product_name,
        "Price": price,
        "URL": url
    }])
    wishlist_df = pd.concat([wishlist_df, new_entry], ignore_index=True)
    wishlist_df.to_excel(wishlist_file, index=False)

# ✅ Route: Login Page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["username"] = request.form.get("username")
        return redirect(url_for("first_page"))
    return render_template("login.html")

# ✅ Route: First Page
@app.route("/first")
def first_page():
    username = session.get("username", "Guest")
    return render_template("first.html", username=username)

# ✅ Route: Product Selection Page
@app.route("/index/<category>")
def index_page(category):
    if category not in ["mobiles", "headsets", "speakers", "tablets", "smartwatches"]:
        return "Invalid category", 400
    return render_template("index.html", category=category)

# ✅ API: Get Product List
@app.route("/products/<category>")
def get_products(category):
    df = {
        "mobiles": mobiles_df,
        "headsets": headsets_df,
        "speakers": speakers_df,
        "tablets": tablets_df,
        "smartwatches": smartwatches_df
    }.get(category)

    if df is None or df.empty:
        return jsonify({"message": "No data available"}), 500

    return jsonify({"products": df["name"].unique().tolist()})

# ✅ API: Compare Prices
@app.route("/compare/<category>/<product_name>")
def compare_prices(category, product_name):
    df = {
        "mobiles": mobiles_df,
        "headsets": headsets_df,
        "speakers": speakers_df,
        "tablets": tablets_df,
        "smartwatches": smartwatches_df
    }.get(category)

    if df is None or df.empty:
        return jsonify({"message": "No data available"}), 500

    product_name = product_name.strip().lower()
    product_data = df[df["name"] == product_name]

    if product_data.empty:
        return jsonify({"message": "Product not found"}), 404

    amazon_price = str(product_data["amazon"].values[0]) if "amazon" in df.columns else "N/A"
    flipkart_price = str(product_data["flipkart"].values[0]) if "flipkart" in df.columns else "N/A"

    return jsonify({
        "product_name": product_name,
        "price_comparison": [
            {"platform": "Amazon", "price": amazon_price},
            {"platform": "Flipkart", "price": flipkart_price}
        ]
    })

# ✅ API: Add to Wishlist
@app.route("/add_to_wishlist", methods=["POST"])
def add_to_wishlist_route():
    data = request.json
    add_to_wishlist(data["category"], data["product_name"], data["price"], data["url"])
    return jsonify({"message": "Product added to wishlist successfully!"})

# ✅ Wishlist Page (serve HTML page)
@app.route("/wishlist")
def wishlist_page():
    return render_template("wishlist.html")

# ✅ Wishlist File Download
@app.route("/download_wishlist")
def download_wishlist():
    return send_file(wishlist_file, as_attachment=True)

# ✅ Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

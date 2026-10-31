function el(id) {
	return document.getElementById(id);
}


function peso(amount) {
	return "₱" + Number(amount).toFixed(2);
}

function safe(text) {
 	text = String(text);
 	text = text.replace(/&/g, "&amp;");
  	text = text.replace(/</g, "&lt;");
  	text = text.replace(/>/g, "&gt;");
  	text = text.replace(/"/g, "&quot;");
  	text = text.replace(/'/g, "&#39;");
 	return text;
}


async function callApi(url, method, body) {
  	const options = { method: method || "GET" };

  	if (body) {
    		options.headers = { "Content-Type": "application/json" };
    		options.body = JSON.stringify(body); // turn the object into text
  	}

  	const response = await fetch(url, options);

  	let data = null;
  	try {
    		data = await response.json();
  	} catch (error) {}

	
	if (!response.ok) {
    		let message = response.statusText;
    		if (data && data.detail) {
      			message = data.detail;
    		}
    	throw new Error(message);
  	}
  	return data;
}



function expiryHtml(product) {
	if (product.status === "none") {
		return '<span class="badge none">No expiry</span>';
	}

	let label = "";
	if (product.status === "expired"){
		label = "Expired " + Math.abs(product.days_left) + "d ago";

	} else if (product.days_left === 0) {

		label = "Expires today";
	} else{

	label = product.days_left + " days left";
  	}

  	return '<span class="badge ' + product.status + '">' + label + "</span> <small>" + safe(product.expiry) + "</small>";
}


function showProducts(products, emptyMessage) {
	const tableBody = el("rows");

	if (products.length === 0) {
		tableBody.innerHTML = '<tr><td colspan="7" class="empty">' + emptyMessage + "</td></tr>";
	return;
	}

  	let html = "";
  	for (let i = 0; i < products.length; i++) {
   		const p = products[i];


    		let stockClass = "";
    		if (p.quantity <= 5) {
      			stockClass = "low";
    		}

    		html += "<tr>";
    		html += "<td>" + safe(p.sku) + "</td>";
    		html += "<td>" + safe(p.name) + "</td>";
    		html += "<td>" + safe(p.category) + "</td>";
    		html += '<td class="num">' + peso(p.price) + "</td>";
    		html += '<td class="num ' + stockClass + '">' + p.quantity + "</td>";
    		html += "<td>" + expiryHtml(p) + "</td>";
    		html += '<td class="actions-cell">';
    		html += '<button class="btn small" onclick="openSell(\'' + p.sku + '\')">Sell</button>';
    		html += '<button class="btn small" onclick="editProduct(\'' + p.sku + '\')">Edit</button>';
    		html += '<button class="btn small danger" onclick="deleteProduct(\'' + p.sku + '\')">Delete</button>';
    		html += "</td>";
    		html += "</tr>";
  	}
  	tableBody.innerHTML = html;
}


async function loadProducts(){
	const searchText = el("q").value.trim();

  	try {
    		if (searchText !== ""){

      			const url = "/api/search?q=" + encodeURIComponent(searchText) + "&mode=" + el("mode").value;
      			const result = await callApi(url);
      			showProducts(result.items, 'No product matches "' + safe(searchText) + '". Try fewer letters or the other search method.');
      			el("info").textContent = result.items.length + " found using " + result.algorithm + ", " + result.steps + " steps checked.";
    		} else{

      			const url = "/api/products?sort_by=" + el("sortBy").value + "&order=" + el("order").value + "&algo=" + el("algo").value;
      			const result = await callApi(url);
      			showProducts(result.items, "No products yet. Use “Add product” to create the first one.");
      			el("info").textContent = result.items.length + " products sorted with " + result.algorithm + " in " + result.ms + " ms.";
    		}	
  	} catch (error) {
    		el("info").textContent = error.message;
  	}
}

async function loadExpiring(){
	const products = await callApi("/api/expiring?limit=5");

  	if (products.length === 0) {
    		el("tags").innerHTML = '<p class="hint">No products with expiry dates yet.</p>';
   	 return;
  	}

  	let html = "";
  	for (let i = 0; i < products.length; i++) {
    		const p = products[i];

    		let when = "";
    		if (p.status === "expired") {
      			when = "Expired " + Math.abs(p.days_left) + "d ago";
    		} else {
      			when = p.days_left + " days left";
    		}

    		html += '<div class="tag ' + p.status + '">';
    		html += "<strong>" + safe(p.name) + "</strong>";
    		html += '<span class="when">' + when + "</span>";
    		html += '<span class="sub">' + safe(p.expiry) + " · " + p.quantity + " in stock</span>";
    		html += "</div>";
  	}
  	el("tags").innerHTML = html;
}


async function loadPriceRange() {
	el("rangeErr").textContent = "";

  	const low = el("minP").value;
  	const high = el("maxP").value;

  	if (low === "" || high === "") {
    		el("rangeErr").textContent = "Enter both a minimum and a maximum price.";
    		return;
  	}

  	try {
    		const products = await callApi("/api/price-range?min_price=" + low + "&max_price=" + high);

    		if (products.length === 0) {
     			el("rangeOut").innerHTML = "<li>No products priced between " + peso(low) + " and " + peso(high) + ".</li>";
      			return;
    	}

    	let html = "";
    	for (let i = 0; i < products.length; i++) {
      	html += "<li><span>" + safe(products[i].name) + "</span><strong>" + peso(products[i].price) + "</strong></li>";

    	}
    	el("rangeOut").innerHTML = html;
  	} catch (error){
    		el("rangeErr").textContent = error.message;
    		el("rangeOut").innerHTML = "";
  	}
}

async function loadStructures() {
	const s = await callApi("/api/structures");


  	let biggest = 1;
 	 for (let i = 0; i < s.bucket_lengths.length; i++) {
    		if (s.bucket_lengths[i] > biggest) {
      		biggest = s.bucket_lengths[i];

    		}
  	}

  	let bars = "";
  	for (let i = 0; i < s.bucket_lengths.length; i++) {
    		const count = s.bucket_lengths[i];
    		let height = (count / biggest) * 100;

    		if (height < 4) {
      			height = 4; 
    		}

    		bars += '<span style="height:' + height + '%" title="' + count + ' item(s)"></span>';
  	}


  	let chips = "";
  	for (let i = 0; i < s.heap.top.length; i++) {
		chips += "<span>" + safe(s.heap.top[i][0]) + " " + safe(s.heap.top[i][1]) + "</span>";
  	}


 	 let rootText = "";
  	if (s.bst.root) {
    		rootText = ", root " + peso(s.bst.root[0]) + " (" + safe(s.bst.root[1]) + ")";
  	}
  	let latestText = "";
  	if (s.stack.top) {
   		latestText = ", latest: " + safe(s.stack.top.name) + " × " + s.stack.top.quantity;
  	}

  	el("structs").innerHTML =
    	"<h3>Hash table (SKU lookup)</h3>" +
    	"<p>" + s.hash_table.size + " items in " + s.hash_table.capacity + " buckets, load " + s.hash_table.load_factor + ", longest chain " + s.hash_table.longest_chain + "</p>" +
    	'<div class="buckets">' + bars + "</div>" +
    	"<h3>Min-heap (expiry), first " + s.heap.top.length + " of " + s.heap.size + "</h3>" +
    	'<div class="chips">' + chips + "</div>" +
    	"<h3>Stack (sales log)</h3>" +
    	"<p>" + s.stack.size + " sales" + latestText + "</p>" +
    	"<h3>Binary search tree (price)</h3>" +
    	"<p>" + s.bst.size + " nodes, height " + s.bst.height + rootText + "</p>";
}

async function loadSales(){
	const sales = await callApi("/api/sales?limit=8");
  	const report = await callApi("/api/sales/report");

  	if (sales.length === 0) {
    		el("saleList").innerHTML = "<li>No sales yet. Use Sell on a product to record one.</li>";
  	} else{
    		let html = "";
    		for (let i = 0; i < sales.length; i++) {
      			const sale = sales[i];
      			const time = sale.sold_at.slice(0, 16).replace("T", " "); 
      			html += '<li class="sale"><span>' + safe(sale.name) + " × " + sale.quantity;
      			html += "<small>" + safe(time) + "</small></span>";
      			html += "<strong>" + peso(sale.total) + "</strong></li>";
    		}
    	el("saleList").innerHTML = html;
 	}


  	el("undoBtn").disabled = (sales.length === 0);


  	if (report.count === 0) {
    		el("report").innerHTML = '<p class="hint">The report appears after the first sale.</p>';
    		return;
  	}

  	let bestHtml = "";
  	for (let i = 0; i < report.best_sellers.length; i++) {
    		const item = report.best_sellers[i];
   		 bestHtml += "<li><span>" + safe(item.name) + " (" + item.units + ")</span><strong>" + peso(item.revenue) + "</strong></li>";
  	}

 	let daysHtml = "";
  	for (let i = 0; i < report.by_day.length; i++) {
    		const day = report.by_day[i];
    		daysHtml += "<li><span>" + safe(day.day) + " (" + day.sales + " sales)</span><strong>" + peso(day.revenue) + "</strong></li>";
  	}

  	el("report").innerHTML =
    	'<p class="report-total">' + peso(report.revenue) + "</p>" +
    	'<p class="hint">' + report.count + " sales, " + report.units + " items sold</p>" +
    	"<h4>Best sellers by revenue</h4>" +
   	'<ul class="plain">' + bestHtml + "</ul>" +
   	"<h4>Daily totals</h4>" +
    	'<ul class="plain">' + daysHtml + "</ul>";
}


async function refreshAll() {
 	try {
    		await loadProducts();
    		await loadExpiring();
    		await loadStructures();
    		await loadSales();


    		if (el("rangeOut").children.length > 0) {
      			await loadPriceRange();
    		}
  	} catch (error){
    		el("info").textContent = error.message;
  	}
}




let editingSku = null;

const formFields = ["sku", "name", "category", "price", "quantity", "expiry"];


function openForm(product) {
  	el("formErr").textContent = "";

 	if (product) {
    		editingSku = product.sku;
    		el("formTitle").textContent = "Edit " + product.sku;
    		el("f_sku").disabled = true; 
  	} else{
    		editingSku = null;
    		el("formTitle").textContent = "Add product";
    		el("f_sku").disabled = false;
  	}


  	for (let i = 0; i < formFields.length; i++) {
    		const field = formFields[i];
    		let value = "";
    		if (product && product[field] !== null) {
      			value = product[field];
    		}
    		el("f_" + field).value = value;
 	}

 	el("formDlg").showModal();
}


async function editProduct(sku) {
 	try {
    		const product = await callApi("/api/products/" + encodeURIComponent(sku));
    		openForm(product);
  	} catch (error) {
    		el("info").textContent = error.message;
    		await refreshAll();
  	}
}


async function saveProduct(event) {
  	event.preventDefault(); 

  	const data = {
    		name: el("f_name").value.trim(),
    		category: el("f_category").value.trim(),
    		price: parseFloat(el("f_price").value),
    		quantity: parseInt(el("f_quantity").value, 10),
    		expiry: null
  	};

  	if (el("f_expiry").value !== "") {
    		data.expiry = el("f_expiry").value;
  	}


  	if (isNaN(data.price) || isNaN(data.quantity)) {
    		el("formErr").textContent = "Price and stock must be numbers.";
    		return;
  	}

 	 try {
    		if (editingSku !== null) {

      			await callApi("/api/products/" + encodeURIComponent(editingSku), "PUT", data);
    		} else {

      			data.sku = el("f_sku").value.trim();
     			 await callApi("/api/products", "POST", data);
    		}
    	el("formDlg").close();
    	await refreshAll();
  	} catch (error) {
    		el("formErr").textContent = error.message; 
  	}
}


let sellingSku = null;


function openSell(sku) {
  	sellingSku = sku;
  	el("sellTitle").textContent = "Sell " + sku;
  	el("s_qty").value = 1;
  	el("sellErr").textContent = "";
  	el("sellDlg").showModal();
}

async function confirmSale(event) {
  	event.preventDefault();

  	const quantity = parseInt(el("s_qty").value, 10);
  	if (isNaN(quantity)) {
    	el("sellErr").textContent = "Enter the quantity sold.";
   		return;
  	}

  	try {
   		await callApi("/api/products/" + encodeURIComponent(sellingSku) + "/sell", "POST", { quantity: quantity });
    		el("sellDlg").close();
    		el("undoMsg").textContent = "";
    		await refreshAll();
  } catch (error) {
    el("sellErr").textContent = error.message; 
  }
}


async function deleteProduct(sku) {
  	if (!confirm("Delete " + sku + "? This cannot be undone.")) {
    		return; 
  	}

  	try {
    		await callApi("/api/products/" + encodeURIComponent(sku), "DELETE");
    		await refreshAll();
  	} catch (error){
    		el("info").textContent = error.message;
   		 await refreshAll();
  	}
}


async function undoLastSale() {
  	try {
    		const result = await callApi("/api/sales/undo", "POST");

    		if (result.restored) {
      			el("undoMsg").textContent = "Undid sale of " + result.sale.quantity + " × " + result.sale.name + ". Stock restored.";
    	} else{
      		el("undoMsg").textContent = "Removed sale of " + result.sale.name + ". The product was deleted, so no stock was restored.";
    	}
    	await refreshAll();
  	} catch (error){
    		el("undoMsg").textContent = error.message;
  	}
}





el("addBtn").addEventListener("click", function () { openForm(null); });
el("formCancel").addEventListener("click", function () { el("formDlg").close(); });
el("sellCancel").addEventListener("click", function () { el("sellDlg").close(); });
el("rangeBtn").addEventListener("click", loadPriceRange);
el("undoBtn").addEventListener("click", undoLastSale);


el("form").addEventListener("submit", saveProduct);
el("sellForm").addEventListener("submit", confirmSale);


el("sortBy").addEventListener("change", loadProducts);
el("order").addEventListener("change", loadProducts);
el("algo").addEventListener("change", loadProducts);
el("mode").addEventListener("change", loadProducts);


let searchTimer = null;
el("q").addEventListener("input", function () {
  	clearTimeout(searchTimer);
  	searchTimer = setTimeout(loadProducts, 250);
});


refreshAll();
function addToCart(itemId) {
    fetch('/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ itemId: itemId }),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('totalQuantity').innerText = data.total_quantity;
    })
    .catch(error => console.error('Error:', error));
  }  
function argmin(arr, cmp) {
  var arr2 = _.toArray(arr);
  arr2.sort(cmp);
  return arr2[0];
}

// inject javascript from URL
function insertScript(url) {
  var script = document.createElement('script');
  script.setAttribute("src", url);
  (document.body || document.head || document.documentElement)
      .appendChild(script);
}

// get all text nodes directly under a node
function getTextNodes(el) {
  return $(el).find(":not(iframe)").addBack().contents().filter(function() {
    return this.nodeType == 3;
  });
}

// extract all listed products
function extractProducts(context) {
  var products = $("tr.tm", context)
      .filter(function() {
        return $(this).children().length === 4;
      })
      .map(function() {
        var td                  = $(this).find("td");

        var condition           = $(td[1]).find("b").text().toLowerCase();

        var product_name        = getTextNodes(td[2])[0].textContent.trim();

        var product_id          = $(td[2]).find("font.fv a:last-child").text();

        var td_quantity         = $(td[3]),
            available_quantity  = +$(td_quantity.find("b")[0]).text().replace(",", ""),
            price               = +$(td_quantity.find("b")[1]).text().slice(4).replace(",", ""),
            wanted_quantity     = +$(td_quantity.find("font.fv b")[0]).text().replace(",", "");

        var input               = $(this).find("input:text");

        return {
          'product_id': product_id,
          'condition': condition,
          'available_quantity': available_quantity,
          'price': price,
          'wanted_quantity': wanted_quantity,
          'input': input,
          'name': product_name
        }
      });
  return products;
}

// choose how much to buy of each product
function allocateQuantity(products) {
  // prefer cheaper products, then new products on ties
  var comparator = function(left, right) {
    if (left.price < right.price) {
      return -1;
    } else if (left.price === right.price) {
      if (left.condition === 'new') {
        return -1;
      } else {
        return +1;
      }
    } else {
      return +1;
    }
  };

  var result = [];

  _.pairs(_.groupBy(products, 'name'))
      .forEach(function(pair) {
        var product_id = pair[0],
            products = pair[1],
            wanted_quantity = products[0].wanted_quantity;

        products.sort(comparator);

        products.forEach(function(p_) {
          var p = _.clone(p_),
              amount = Math.min(wanted_quantity, p.available_quantity);

          if (amount > 0) {
            p.allocation = amount;
            wanted_quantity = wanted_quantity - amount;
          } else {
            p.allocation = 0;
          }

          result.push(p);
        });
      });
  return result;
}

////////////////////////////////////////////////////////////////////////////////

insertScript("http://code.jquery.com/jquery-1.9.0.min.js");
insertScript("http://underscorejs.org/underscore-min.js");

function run() {
  var context = $("frame[name='blstoremain']").get(0).contentDocument,
      products = extractProducts(context),
      products2 = allocateQuantity(products);

  // put in value
  products2.forEach(function(d) {
    if (d.allocation > 0) {
      d.input.attr("value", d.allocation);
    } else {
      d.input.attr("value", "")
    }
  });
}

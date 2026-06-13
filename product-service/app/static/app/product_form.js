(function(){
  const form = document.getElementById('product-form');
  const subtype = document.getElementById('subtype-fields');
  const typeSelect = document.getElementById('product_type');
  const catSelect = document.getElementById('category_id');
  const result = document.getElementById('result');
  
  let allCategories = [];

  function clearSubtype(){ subtype.innerHTML = ''; }

  function createField(name, label, type='text', attrs={}){
    const wrap = document.createElement('label');
    wrap.textContent = label + ': ';
    const input = document.createElement('input');
    input.name = name;
    input.type = type;
    Object.keys(attrs).forEach(k=> input.setAttribute(k, attrs[k]));
    wrap.appendChild(input);
    return wrap;
  }

  function showFieldsFor(type){
    clearSubtype();
    if(type === 'BOOK'){
      subtype.appendChild(createField('author','Author'));
      subtype.appendChild(createField('publisher','Publisher'));
      subtype.appendChild(createField('publication_date','Publication Date','date'));
      subtype.appendChild(createField('language','Language'));
      subtype.appendChild(createField('isbn','ISBN'));
    }
    if(type === 'ELECTRONICS'){
      subtype.appendChild(createField('model_name','Model'));
      subtype.appendChild(createField('brand','Brand'));
      subtype.appendChild(createField('warranty','Warranty (months)','number',{min:0}));
      subtype.appendChild(createField('weight','Weight (kg)','number',{step:'0.01',min:0}));
      subtype.appendChild(createField('dimensions','Dimensions (LxWxH)'));
      subtype.appendChild(createField('color','Color'));
    }
    if(type === 'FASHION'){
      subtype.appendChild(createField('brand','Brand'));
      subtype.appendChild(createField('size','Size'));
      subtype.appendChild(createField('color','Color'));
      subtype.appendChild(createField('material','Material'));
      subtype.appendChild(createField('season','Season'));
      subtype.appendChild(createField('gender','Gender'));
    }
  }

  function updateCategoryFilter(selectedType){
    const selectedCategoryValue = catSelect.value;
    catSelect.innerHTML = '<option value="">--Chọn--</option>';
    allCategories.forEach(c=>{
      if(c.product_type === selectedType){
        const o = document.createElement('option');
        o.value = c.id;
        o.textContent = c.name;
        o.selected = (c.id == selectedCategoryValue);
        catSelect.appendChild(o);
      }
    });
  }

  typeSelect.addEventListener('change', e=>{
    showFieldsFor(e.target.value);
    updateCategoryFilter(e.target.value);
  });

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  async function loadCategories(){
    try{
      const res = await fetch('/categories/');
      const payload = await res.json();
      allCategories = Array.isArray(payload) ? payload : (payload.results || []);
      updateCategoryFilter(typeSelect.value || 'ELECTRONICS');
    }catch(err){ console.error(err); }
  }

  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const formData = new FormData(form);
    const payload = {};
    formData.forEach((v,k)=>{ payload[k]= v; });

    try{
      const csrf = getCookie('csrftoken');
      const res = await fetch('/products/',{
        method: 'POST',
        headers: {'Content-Type':'application/json', 'X-CSRFToken': csrf || ''},
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if(!res.ok){ result.textContent = JSON.stringify(data, null, 2); return; }
      result.textContent = 'Created:\n' + JSON.stringify(data, null, 2);
    }catch(err){ result.textContent = err.toString(); }
  });

  loadCategories();
})();

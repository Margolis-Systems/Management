let newWindow;
const shapeData = document.getElementById('shape_data');
const formInput = document.getElementById('shape');
const lengInput = document.getElementById('length');
const widtInput = document.getElementById('width');

const openEditWindow = (editorUrl) => {
    const params = `scrollbars=no,resizable=no,status=no,location=no,toolbar=no,menubar=no,width=700,height=500,top=200,left=400`;
    if (formInput.value.length == 0||formInput.value == "undefined"){
        newWindow = window.open(editorUrl, 'sub', params);
    }
    else{
        newWindow = window.open(editorUrl+"?"+formInput.value, 'sub', params);
    }
};

const openNewWindow = (editorUrl) => {
    const params = `scrollbars=no,resizable=no,status=no,location=no,toolbar=no,menubar=no,width=700,height=500,top=200,left=400`;
    newWindow = window.open(editorUrl, 'sub', params);
};

const sendMessage = () => {
    newWindow.postMessage({ foo: 'bar' }, '*');
};

const closeWindow = (shape_selected, tot_len, shape_dt) => {
    window.opener.postMessage({shp: shape_selected, len: tot_len, shapedt: shape_dt}, '*');
    window.close();
};

const refreshWindow = () => {
    setTimeout(function(){
   window.opener.location.reload();
}, 1000);
setTimeout("window.close()",1000)
};

window.addEventListener('message', (event) => {
    console.log(event.data)
    shapeData.value = event.data.shapedt;
    formInput.value = event.data.shp;
    lengInput.value = event.data.len;
});

function confirmDel() {
  let text = "Are you sure?";
  if (confirm(text) == true) {
    window.location.href = "close?delete";
  }
}

function findTotal(src, target){
    var arr = document.getElementsByClassName(src);
    var tot=0;
    for(var i=0;i<arr.length;i++){
        if(parseFloat(arr[i].value))
            tot += parseFloat(arr[i].value);
    }
    document.getElementById(target).value = tot;
}

function findTotal2(src, target, inputId){
    var inputEl = document.getElementById(inputId)
    var arr = document.getElementsByClassName(src);
    var tot=0
    if (parseFloat(inputEl.value)){
    tot += parseFloat(inputEl.value);
    }
    for(var i=0;i<arr.length;i++){
        if(parseFloat(arr[i].textContent))
            tot += parseFloat(arr[i].textContent);
    }

    if(tot > 0){
        document.getElementById(target).value = tot;
    }
}
var temp = 0
function addInput(div_id, val){
    var container = document.getElementById(div_id);
    var input = document.createElement("input");
    input.type = "number";
    input.name = div_id.replace('_container', temp);
    input.id = div_id.replace('_container', temp);
    temp += 1
    input.setAttribute('class', 'form-control');
    input.setAttribute('onkeydown', "return event.key != 'Enter';");
    input.setAttribute('onkeyup', "");
    if(val){
        input.setAttribute('value', val);
    }
    if(div_id.includes("pitch")){
        input.setAttribute('placeholder', 'פסיעה');
    }
    if(div_id.includes("length")){
        input.setAttribute('placeholder', 'אורך');
    }
    if(div_id.includes("width")){
        input.setAttribute('placeholder', 'רוחב');
    }
    container.appendChild(input);
}

function _addInput(table_id, val){
    var table = document.getElementById(table_id);
    var row = table.insertRow(14);
    var cell1 = row.insertCell(0);
    row.cells[0].className = 'input-group';
    row.cells[0].innerHTML = "<span class='input-group-text'>נפח</span><input type='number' name='' id='hh' placeholder='נפח' class='form-control' autofocus required><button type='button' onclick=''>-</button>";
}

function copyLastRow(dict, dataToDisplay){
    dataToDisplay['shape_data'] = 1;
    dataToDisplay['length'] = 1;
    dataToDisplay['quantity'] = 2;
    dataToDisplay['weight'] = 2;
    for(item in dataToDisplay){
        if(dataToDisplay[item] != 2 && dataToDisplay[item] != 4){
        // validate no undefind
            try {
                document.getElementById(item).value = dict[item];
            }
            catch (error) {
                document.getElementById(item).value = dict[item].map(String);
                console.error(error);
            }
        }
    }
    document.getElementById('quantity').focus();
}

function calc_weight(){
diam = document.getElementById('diam');
qnt = document.getElementById('quantity');
weight = document.getElementById('weight');
weights_list = {
    "6": 0.223,
    "8": 0.398,
    "10": 0.621,
    "12": 0.883,
    "14": 1.213,
    "16": 1.582,
    "18": 2,
    "20": 2.466,
    "22": 2.98,
    "25": 3.864,
    "28": 4.834,
    "32": 6.31,
    "36": 7.986,
    "5.5": 0.2,
    "6.5": 0.27
  };
    leng = lengInput.value;
    if (diam.value){
        weight.value = (leng * qnt.value * weights_list[diam.value] / 100).toFixed(1);
    }
}
function formSubmit(){
    form = document.getElementById("input_form");
        if (form.checkValidity()){
            form.submit();
        }
}

var do_once = 0
function focusNext(inputIndex) {
// reorder func
    inputNames = dtd_order;
    if (event.keyCode === 13){
        var safety = 0;
        while (safety < 20){
            form = document.getElementById("input_form");
            if (form.checkValidity() && do_once==0){
                do_once = 1;
                form.submit();
                break
            }
            inputIndex += 1;
            if (inputIndex >= inputNames.length && do_once == 0){
                if (inputIndex >= inputNames.length){
                    inputIndex = 0;
                }
                //if (shapeData){
                //    if (shapeData.value == "") {
                //        alert("נדרשים פרטי צורה");
                //    }
                //}

            }
            if (datatodisp[inputNames[inputIndex]] != 2 && document.getElementById(inputNames[inputIndex]) !== null){
                inputName = inputNames[inputIndex];
                break
            }
            safety += 1;
        }
        document.getElementById(inputName).focus();
    }
}

function runScanner(order_id){
try{
    fetch("/file_listener", {
      method: "POST"
    });
    }catch (error){
    window.alert("Server Error", error);
}
try{
    fetch("http://localhost:5000/scanner?"+order_id, {
      method: "POST"
    });
}catch (error){
    window.alert("Client Error", error);
}
};

function delete_rows(){
    let selected = []
    select = document.getElementsByClassName('select');
    for(i=0;i<select.length;i++){
        item = select[i];
        if (item.checked) {
            selected.push(item.value)
        }
    }
    if(selected.length > 0){
        document.getElementById('delete_rows_btn').disabled = true;
        form = document.getElementById('input_form');
        form.action = location.href='\\delete_rows'
        form.submit();
    }
}


var expanded = false;

function showCheckboxes() {
  var checkboxes = document.getElementById("checkboxes");
  if (!expanded) {
    checkboxes.style.display = "block";
    expanded = true;
  } else {
    checkboxes.style.display = "none";
    expanded = false;
  }
}

function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + (exdays*24*60*60*1000));
  let expires = "expires="+ d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}
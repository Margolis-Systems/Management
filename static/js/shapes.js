let newWindow;
const shapeData = document.getElementById('shape_data');
const formInput = document.getElementById('editor');
const lengInput = document.getElementById('length');
const widtInput = document.getElementById('width');

const openNewWindow = (editorUrl) => {
    const params = `scrollbars=no,resizable=no,status=no,location=no,toolbar=no,menubar=no,width=700,height=500,top=200,left=400`;
    if (formInput.value.length == 0||formInput.value == "לחץ פעמיים"){
        newWindow = window.open(editorUrl, 'sub', params);
    };
};

const sendMessage = () => {
    newWindow.postMessage({ foo: 'bar' }, '*');
};

const closeWindow = (shape_selected) => {
    window.opener.postMessage({shp: shape_selected}, '*');
    window.close();
};

window.addEventListener('message', (event) => {
    shapeData.value = event.data.shp;
    formInput.value = event.data.shp;
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
    document.getElementById(target).value = tot;
}

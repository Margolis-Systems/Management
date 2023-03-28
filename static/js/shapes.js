let newWindow;
const shapeData = document.getElementById('shape_data');
const shape = document.getElementById('צורה');

const openNewWindow = () => {
if (shape.value.length == 0){
  const params = `scrollbars=no,resizable=no,status=no,location=no,toolbar=no,menubar=no,width=700,height=500,top=200,left=400`;
  newWindow = window.open('/shape_editor', 'sub', params);
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
shape.value = event.data.shp;
});

function confirmDel() {
  let text = "Are you sure?";
  if (confirm(text) == true) {
    window.location.href = "close?delete";
  }
}

function findTotal(){
    var arr = document.getElementsByClassName('amount');
    var tot=0;
    for(var i=0;i<arr.length;i++){
        if(parseFloat(arr[i].value))
            tot += parseFloat(arr[i].value);
    }
    document.getElementById('formtotal').value = tot;
}

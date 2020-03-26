
$('#sendFilters').click(function(){
  var arr=[]
  begin__gte = $('#begin').val();
  begin__lte = $('#begin1').val();
  end__gte = $('#end').val();
  end__lte = $('#end1').val();
  ins__gte = $('#ins').val();
  ins__lte = $('#ins1')
  if (begin__gte) {
    begin__gte = 'begin__gte=' + begin__gte;
    arr.push(begin__gte)
  } else {begin__gte = '';};
  if (begin__lte) {
    begin__lte = 'begin__lte=' + begin__lte;
    arr.push(begin__lte)
  } else {begin__lte = '';};

  if (end__gte) {
    end__gte = 'end__gte=' + end__gte;
    arr.push(end__gte)
  } else {end__gte = '';};
  if (end__lte) {
    end__lte = 'end__lte=' + end__lte;
    arr.push(end__lte)
  } else {end__lte = '';};

  if (ins__gte) {
    ins__gte = 'ins__gte=' + ins__gte;
    arr.push(ins__gte)
  } else {ins__gte = '';};
  if (ins__lte) {
    ins__lte = 'ins__lte=' + ins__lte;
    arr.push(ins__lte)
  } else {ins__lte = '';};

  var gurl = arr.join('&')
  $('#te').html(gurl);
  // $.get('/hotadmin/hotelMan/bid/?');
  // window.location = '/hotadmin/hotelMan/bid/?' + 'begin__gte=' + begin__gte;
});

$(document).ready(function(){

  // move tile "Edit" links next to "Edit Source" links
  var $links = $(".edit_links");
  $links.each(function(){
    var $this = $(this);
    var $parent = $this.parents('.tile');
    var $edits = $parent.siblings(".edit-tile-link").detach();
    $this.prepend($edits);
  });

  // Daviz view embeded, "full screen"
  var $cell = $('.cardgraph');
  $cell.find('.js-expander').click(function() {

    var $thisCell = $(this).closest('.cardgraph');
    var $thiscard=$(this);

    if ($thisCell.hasClass('is-collapsed')) {
      $cell.not($thisCell).removeClass('is-expanded').addClass('is-collapsed').addClass('is-inactive');
      $thisCell.removeClass('is-collapsed').addClass('is-expanded');

      var $ifw = $thisCell.find('.iframe-wrapper');
      $ifw.html('');
      var iurl = $ifw.data('iframe-url');
      var width = $ifw.data('iframe-width');
      var height = $ifw.data('iframe-height');


      var iframe = document.createElement('iframe');
      iframe.src = iurl;
      iframe.style.width = width + 'px';
      iframe.style.height = height + 'px';
      iframe.onload = function() {
        iframe.parentNode.classList.remove('is-loading');
      }

      if (($ifw).length > 0) $ifw[0].appendChild(iframe);

      if ($cell.not($thisCell).hasClass('is-inactive')) {
        //do nothing
      } else {
        $cell.not($thisCell).addClass('is-inactive');
      }

    } else {
      $thisCell.removeClass('is-expanded').addClass('is-collapsed');
      $cell.not($thisCell).removeClass('is-inactive');
    }
  });

  $cell.find('.js-collapser').click(function() {
    var $thisCell = $(this).closest('.cardgraph');
    $thisCell.removeClass('is-expanded').addClass('is-collapsed');
    $cell.not($thisCell).removeClass('is-inactive');
  });

  $(".cardgraph").on('click', function(e){
    e.stopPropagation();
    var body=$('body')[0].getBoundingClientRect();
    var card=$(this)[0].getBoundingClientRect(),

    cardleft=card.left+($(this).outerWidth()-$(this).width())/2;
    bodywidth=body.width+($(this).outerWidth()-$(this).width())/2-14;

    $('.card__expander').css({
      'left' : -cardleft,
      'width': bodywidth
    });
    if($(e.target).parent().hasClass('card__inner')){
      var bodytop = $('body').scrollTop();
      $('body').animate({ scrollTop: bodytop + 350 }, 300);
    }
  });

  $(".fa-close").on('click', function(){
    var bodytop = $('body').scrollTop();
    $('body').animate({ scrollTop: bodytop - 350 }, 300);
  });


  $('.expand').on('click', function(){
    $('.indicator-cards').toggleClass('flex-row-warp');
    $('#left-button, #right-button').toggleClass('buttons-hide')
  });


  // Single row listing scroller
  var outer = $('.singlerow-cards-wrapper');

  $('#left-button').click(function () {
    var leftPos = outer.scrollLeft();
    outer.animate({ scrollLeft: leftPos - 300 }, 300);
  });


  $('#right-button').click(function () {
    var leftPos = outer.scrollLeft();
    outer.animate({ scrollLeft: leftPos + 300 }, 300);
  });

});


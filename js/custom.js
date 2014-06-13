//<![CDATA[


$(document).ready(function () {

	//Append a div with hover class to all the LI
	$('#menu li').append('<div class="hover"></div>');


	$('#menu li').hover(
		
		//Mouseover, fadeIn the hidden hover class	
		function() {
			
			$(this).children('div').stop(true, true).fadeIn('1000');	
		
		}, 
	
		//Mouseout, fadeOut the hover class
		function() {
		
			$(this).children('div').stop(true, true).fadeOut('1000');	
		
	}).click (function () {
	
		//Add selected class if user clicked on it
		$(this).addClass('selected');
		
	});

});

//]]>


// Jcarousel


jQuery(document).ready(function() {
    jQuery('#mycarousel').jcarousel();
});

// Fade
jQuery(document).ready(function() {
$('body').hide();
$('body').fadeIn(1000);
});


function closeForm(){
                $("#messageSent").show("slow");
               
           }
	   

	   
	   
	   
	   
	   
	   //]]>
	   
	   

	   


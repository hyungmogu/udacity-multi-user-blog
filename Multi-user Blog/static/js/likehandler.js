function updateLike(blog_id){
	// process callback using response received from server
	// that way, the number of lines will decrease by half.
	var $liked = ($('#like-button').attr('data-liked') == 'true');
	var $url = '/blog/'+blog_id+'/like'
	if($liked){
		$.ajax({
			type: 'POST',
			url: $url,
			dataType: 'json',
			success: function(result){
				if(result['success']){
					$('#number-of-likes').html('Likes: '+result['new_count']);
					$('#like-button').attr('data-liked','false');
					$('#like-button').html('Like This Page');
					$('#like div.result').html(result['success']);
				}
			},
			error: function(error){
				if(error['status']!=404){
					$('#like div.result').html(error['responseText']);	 	
				} else {
					window.location.href = '/blog/not_found';
				};
			}
		});
	} else {
		$.ajax({
			type: 'POST',
			url: $url,
			dataType: 'json',
			success: function(result){
				if(result['error']){
					console.log(result['error']);
				} else {
					$('#number-of-likes').html('Likes: '+result['new_count']);
					$('#like-button').attr('data-liked','true');
					$('#like-button').html('Liked');
					$('#like div.result').html(result['success']);
				}
			},
			error: function(error){
				if(error['status']!=404){
					$('#like div.result').html(error['responseText']);	 	
				} else {
					window.location.href = '/blog/not_found';
				};
			}
		});				
	}
}; 


// Comment Handlers
// Edit Handler
function postComment(THIS,blog_id){
	var $title = $('#new-comment-form input[name=title]').val();
	var $content = $('#new-comment-form textarea[name=texts]').val();
	// Check if submitting title and contents are non-empty.
	if(!($title.length > 0 && $content.length>0)){
		$('#comments div.header div.result').html('Invalid. Title and content must not be empty.');
		return false;
	};
	// If all is well, send data to server.
	$.ajax({
		url: '/blog/'+blog_id+'/comment/new',
		type: 'POST',
		contentType:'application/json',
		dataType: 'json',
		data: JSON.stringify({'title': $title, 'content':$content}),
		processData: false,
		success: function(result){
			if(result['success']){
				// Clear texts in the form
				$('#new-comment-form input').val('');
				$('#new-comment-form textarea').val('');
				// Append new comment in the list of comments
				var $count = localStorage.count;
				$('#comments ul').prepend('<li id="new-comment-'+$count+'" class="comment"><div class="content"><h3 class="title">'+result['title']+'</h3><div class="meta"><span class="author">'+result['author']+'</span><span class="date-created">'+result['date_created']+'</span></div><pre class="texts">'+result['content']+'</pre><div class="options"><button class="edit">Edit</button><button class="delete">Delete</button></div><input type="hidden" value="'+result['id']+'"></div><div class="result"></div></li>');
				$('.comment button.edit').click(function(){renderCommentEdit(this);});
				$('.comment button.delete').click(function(){deleteComment(this);});
				// Display result
				$('#comments div.header div.result').html(result['success']);
			};
		},
		error: function(error){
			if(error['status'] == 400){
				$('#comments div.header div.result').html(error['responseText']);
			} else if(error['status'] == 401) {
				$('#comments div.header div.result').html(error['responseText']);
			} else if(error['status'] == 404){
				window.location.href = '/blog/not_found';
			};
		}
	});
}

function renderCommentEdit(THIS,blog_id){
	var $liId = $(THIS).closest('li').prop('id');
	var $title = $('#'+$liId+' h3.title').html();
	var $content = $('#'+$liId+' div.texts').html();
	var $commentKeyId = $('#'+$liId+' input[type=hidden]').val();
	// Validate user
	var $url = '/blog/'+blog_id+'/comment/validate?id='+$commentKeyId;
	$.ajax({
		url: $url,
		type: 'GET',
		success:function(result){
			if(result['success']){
				var $form = '<div class="edit"><form action=""><div class="form-group"><input type="text" placeholder="title" name="title" value="'+$title+'"></div><div class="form-group"><textarea name="texts" placeholder="Write your comments here.">'+$content+'</textarea></div></form><button class="submit">Submit</button></div>';
				$('#'+$liId+' div.content').css('display','None');
				$('#'+$liId+' div.content').after($form);
				$('.comment button.submit').click(function(){
					submitCommentEdit(this);
				});
	 		};
		},
		error:function(error){
			if(error['status'] == 401){
				$('#'+$liId+' div.result').html(error['responseText']);
			} else {
				$('#'+$liId+' div.result').html(error['responseText']);
			};
		}
	});
}

function submitCommentEdit(THIS,blog_id){
	// Harvest form data.
	var $liId = $(THIS).closest('li').prop('id');
	var $commentKeyId = $('#'+$liId+' input[type=hidden]').val();
	var $newTitle = $('#'+$liId+' input[name=title]').val();
	var $newContent = $('#'+$liId+' textarea[name=texts]').val();
	// Check if submitting title and contents are non-empty.
	if(!($newTitle.length > 0 && $newContent.length>0)){
		$('#'+$liId+' div.result').html($error_400);
		return false;
	};
	// If all is well, send data to server.
	$.ajax({
		url:'/blog/'+blog_id+'/comment/edit',
		type: 'PUT',
		contentType:'application/json',
		dataType: 'json',
		data: JSON.stringify({'title': $newTitle, 'content':$newContent, 'id':$commentKeyId}),
		processData: false,
		success: function(result){
			if(result['success']){
				// Replace the comment with new title and content.
				$('#'+$liId+' h3.title').html($newTitle);
				$('#'+$liId+' div.texts').html($newContent);
				// Remove form and re-display content.
				$('#'+$liId+' div.content').css('display','initial');
				$('#'+$liId+' div.edit').remove();
				// Display result
				$('#'+$liId+' div.result').html(result['success']);
			};
		}, 
		error: function(error){
			if(error['status'] == 400){
				$('#'+$liId+' div.result').html(error['responseText']);
			} else if(error['status'] == 401) {
				window.location.href = '/blog/not_authorized';
			} else if(error['status'] == 404){
				window.location.href = '/blog/not_found';
			};
		}
	});
}

function deleteComment(THIS,blog_id){
	// Harvest comment id.
	var $liId = $(THIS).closest('li').prop('id');
	var $commentKeyId = $('#'+$liId+' input[type=hidden]').val();
	// Send AJAX DELETE request to server.
	$.ajax({
		url: '/blog/'+blog_id+'/comment/delete?id='+$commentKeyId,
		type: 'DELETE',
		dataType:'json',
		success:function(result){
			if(result['success']){
				$('#comments div.header div.result').html(result['success']);
				$('#'+$liId).remove();
			}
		},
		error:function(error){
			if(error['status']==400){
				$('#'+$liId+' div.result').html(error['responseText']);
			} else if(error['status']==401){
				$('#'+$liId+' div.result').html(error['responseText']);
			} else if(error['status']==403){
				$('#'+$liId+' div.result').html(error['responseText']);
			} else if(error['status']==404){
				window.location.href='/blog/not_found';
			}
		}

	});

}
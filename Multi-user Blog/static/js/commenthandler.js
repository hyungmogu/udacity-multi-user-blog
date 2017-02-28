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
			console.log(result)
			if(result['success']){
				$('#comments div.header div.result').html('Comment has been added successfully.');
				// Clear texts in the form
				$('#new-comment-form input').val('');
				$('#new-comment-form textarea').val('');
				// Append new comment in the list of comments
				var $count = localStorage.count;
				$('#comments ul').prepend('<li id="new-comment-'+$count+'" class="comment"><div class="content"><h3 class="title">'+result['title']+'</h3><div class="meta"><span class="author">'+result['author']+'</span><span class="date-created">'+result['date_created']+'</span></div><pre class="texts">'+result['content']+'</pre><div class="options"><button class="edit">Edit</button><button class="delete">Delete</button></div><input type="hidden" value="'+result['id']+'"></div><div class="result"></div></li>');
				$('.comment button.edit').click(function(){render_comment_edit(this);});
				$('.comment button.delete').click(function(){delete_comment(this);});
			};
		},
		error: function(error){
			console.log(error)
			if(error['status'] == 400){
				$('#comments div.header div.result').html('Title and comment must not be empty.');
			} else if(error['status'] == 401) {
				$('#comments div.header div.result').html('User must be logged in to post this comment.');
			} else if(error['status'] == 404){
				window.location.href = '/blog/not_found';
			};
		}
	});
};

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
					submit_comment_edit(this);
				});
	 		};
		},
		error:function(error){
			if(error['status'] == 401){
				$('#'+$liId+' div.result').html('Invalid. Either user is not signed in, or is not the author of this comment.');
			} else {
				console.log(error);
			};
		}
	});
};

function submitCommentEdit(THIS,blog_id){
	var $ERROR_400 = 'Invalid. Both title and content must not be empty.';
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
	console.log({'title': $newTitle, 'content':$newContent, 'id':$commentKeyId});
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
				console.log('This comment has been edited successfully.');
				// Replace the comment with new title and content.
				$('#'+$liId+' h3.title').html($newTitle);
				$('#'+$liId+' div.texts').html($newContent);
				// Remove form and re-display content.
				$('#'+$liId+' div.content').css('display','initial');
				$('#'+$liId+' div.edit').remove();
			};
		}, 
		error: function(error){
			if(error['status'] == 400){
				$('#'+$liId+' div.result').html($error_400);
			} else if(error['status'] == 401) {
				window.location.href = '/blog/not_authorized';
			} else if(error['status'] == 404){
				window.location.href = '/blog/not_found';
			};
		}
	});
}; 

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
				$('#'+$liId).remove();
			}
		},
		error:function(error){
			if(error['status']==400){
				console.log(400);
				$('#'+$liId+' div.result').html('Invalid. Comment is not found.');
			} else if(error['status']==401){
				console.log(401);
				$('#'+$liId+' div.result').html('Invalid. User is not logged in.');
			} else if(error['status']==403){
				console.log(403);
				$('#'+$liId+' div.result').html('Not allowed. User must be the author of this post.');
			} else if(error['status']==404){
				window.location.href='/blog/not_found';
			}
		}

	});

};
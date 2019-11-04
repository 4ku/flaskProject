function changeIndex(form, oldIndex, newIndex){
	form.attr('id', form.attr('id').replace(oldIndex, newIndex));
	form.attr('data-index', form.attr('data-index').replace(oldIndex, newIndex));

	form.find('label').each(function(idx) {
		var $item = $(this);
		$item.attr('for', $item.attr('for').replace(oldIndex, newIndex));

	});

	form.find('input').each(function(idx) {
		var $item = $(this);
		$item.attr('id', $item.attr('id').replace(oldIndex, newIndex));
		$item.attr('name', $item.attr('name').replace(oldIndex, newIndex));
	});
	form.find('textarea').each(function(idx) {
			var $item = $(this);
			$item.attr('id', $item.attr('id').replace(oldIndex, newIndex));
			$item.attr('name', $item.attr('name').replace(oldIndex, newIndex));
	});
	form.find('select').each(function(idx) {
		var $item = $(this);
		$item.attr('id', $item.attr('id').replace(oldIndex, newIndex));
		$item.attr('name', $item.attr('name').replace(oldIndex, newIndex));
	});

}
	
function adjustIndices(removedIndex, class_) {


	var $forms = $('.'+class_);
	$forms.each(function(i) {
		var $form = $(this);
		var index = parseInt($form.attr('data-index'));
		var newIndex = index - 1;
		if (index < removedIndex) {
			// Skip
			return true;
		}

		changeIndex($form, index, newIndex);
	});
}


function removeForm() {
	var class_ =$(this).parent().attr('class');
	var $removedForm = $(this).closest('.'+class_);
	var removedIndex = parseInt($removedForm.attr('data-index'));

	var total_removedIndex;
	$removedForm.find("[name$=-order]").each(function(idx) {
		total_removedIndex = $(this).val()
	});

	$removedForm.remove();

	// Change order index
	var $all_forms = $("#fields-container").children()
	$all_forms.each(function(i) {
		var $form = $(this);
		var index;
		$form.find("[name$=-order]").each(function(idx) {
			index = $(this).val()
		});
		var newIndex = index - 1;
		if (index < total_removedIndex) {
			// Skip
			return true;
		}
		$form.find("[name$=-order]").each(function(idx) {
			$(this).val(newIndex)
		});
	});

	// Update indices
	adjustIndices(removedIndex, class_);
}

function addForm(e) {
	e.preventDefault();
	var field_type = $("#fields_list").children("option:selected").val();
	var id_ = 0;
	var class_ = 0;
	if (field_type === "Text"){
		id_ = "text_fields-___-form"
		class_ = "text_fields"
	}
	else if (field_type === "TextArea"){
		id_ = "textArea_fields-___-form"
		class_ = "textArea_fields"
	}
	else if (field_type === "Date"){
		id_ = "date_fields-___-form"
		class_ = "date_fields"
	}
	else if (field_type === "Link"){
		id_ = "link_fields-___-form"
		class_ = "link_fields"
	}
	else if (field_type === "File"){
		id_ = "file_fields-___-form"
		class_ = "file_fields"
	}
	else if (field_type === "Picture"){
		id_ = "picture_fields-___-form"
		class_ = "picture_fields"
	}
	var $templateForm = $('#'+id_);
	var $lastForm = $('.'+class_).last();
	var newIndex = 0;
	if ($lastForm.length > 0) {
		newIndex = parseInt($lastForm.data('index')) + 1;
	} 

	var $newForm = $templateForm.clone();

	var numFields = $('#fields-container').children('div').length
	$newForm.find('#'+class_+'-___-order').val(numFields)

	changeIndex($newForm, '___', newIndex);

	$('#fields-container').append($newForm);
	$newForm.addClass(class_);
	// $newForm.css('display', 'flex');
	$newForm.css({'order': numFields,'display':'flex'});

	$newForm.find('.remove').click(removeForm);
}

$(document).ready(function() {
	$('#add_field').click(addForm);
	$('.remove').click(removeForm);
});

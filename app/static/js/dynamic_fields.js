function make_replace(item, attr_name, oldIndex, newIndex){
	var attr = item.attr(attr_name);
	if (typeof attr !== typeof undefined && attr !== false) {
		item.attr(attr_name, item.attr(attr_name).replace(oldIndex, newIndex));
	}
}

function changeIndex(form, oldIndex, newIndex){
	form.attr('id', form.attr('id').replace(oldIndex, newIndex));
	form.attr('data-index', form.attr('data-index').replace(oldIndex, newIndex));
	form.find('label, input, textArea, select, div, a').each(function(idx) {
		var $item = $(this);
		make_replace($item, "id", oldIndex, newIndex)
		make_replace($item, "name", oldIndex, newIndex)
		make_replace($item, "for", oldIndex, newIndex)
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
	var class_ = $(this).parent().attr('class');
	var $removedForm = $(this).parent();
	var removedIndex = parseInt($removedForm.attr('data-index'));

	var total_removedIndex;
	var total_removedIndex = $removedForm.find("[name$=-order]").val()

	$removedForm.remove();

	// Change order index
	var $all_forms = $("#fields-container").children()
	$all_forms.each(function(i) {
		var $form = $(this);
		var index = $form.find("[name$=-order]").val()
		if (index < total_removedIndex) {
			// Skip
			return true;
		}
		$form.find("[name$=-order]").val(index-1)
	});

	// Update indices
	adjustIndices(removedIndex, class_);
}

function addForm(newForm, class_, append_to_id){

	// Вычисляем индекс нового поля нужного типа 
	var newIndex = $('.' + class_).length
	
	changeIndex(newForm, '___', newIndex);
	
	newForm.addClass(class_);
	newForm.find('.remove').click(removeForm);
	$(append_to_id).append(newForm);

	// Добавление порядка - записываем в css и поле order
	// Вычиляем сколько всего полей
	var numFields = $(append_to_id).children('div').length
	// Заполняем порядковый номер нового поля
	newForm.find('#'+class_+'-___-order').val(numFields)
	newForm.css({'order': numFields,'display':'flex'});	
}

function addFieldForm(e) {
	e.preventDefault();

	// fields_list - кнопка из AddForm
	var field_type = $("#fields_list").children("option:selected").val();

	var prefix;
	
	if (field_type === "Text"){
		prefix = "text"
	}
	else if (field_type === "TextArea"){
		prefix = "textArea"
	}
	else if (field_type === "Date"){
		prefix = "date"
	}
	else if (field_type === "Link"){
		prefix = "link"
	}
	else if (field_type === "File"){
		prefix = "file"
	}
	else if (field_type === "Picture"){
		prefix = "picture"
	}
	else if (field_type === "Number"){
		prefix = "number"
	}
	else if (field_type === "Categories"){
		prefix = "categories"
	}

	var id_ = prefix + "_fields-___-form"
	var class_ = prefix + "_fields"

	// Берём шаблон нужного типа и клонируем 
	var $newForm = $('#' + id_).clone();

	addForm($newForm, class_, '#fields-container')

	if (field_type === "Categories"){
		$newForm.find('#add_category').click(add_category);
	}
}

function add_category(){
	var id_ ="categories_fields-xxx-categories-___-category-form"
	var $newForm = $('#' + id_).clone();
	var categories_id = $(this).parent().attr("id")
	var categories_number = parseInt(categories_id.substring("categories-".length, categories_id.length))
	changeIndex($newForm, 'xxx', categories_number);
	var class_ = "categories-" + categories_number
	addForm($newForm, class_, "#" + categories_id)
}

$(document).ready(function() {
	$('#add_field').click(addFieldForm);
	$('.remove').click(removeForm);
});

/*
 *  Genric Model
 *  
 *  args:
 *    * obj: the object this model represents
 *  
 *  methods:
 *    * deleteObject: Delete the model
 */
var Model = function(obj) {
    this.name = ko.observable(obj.name);
    this.title = this.name().replace(/_/gi, ' ');
    this.formVisible = ko.observable(false);

    this.toggleForm = function() {
        this.formVisible(!this.formVisible());
    };

    this.deleteObject = function() {
        jQuery.ajax({
            url : this.url,
            type : 'DELETE',
            success : $.proxy(function(data) {
                if(this.onDelete) {
                    this.onDelete(this);
                }
            }, this)
        });
    };
};

var Group = function(obj) {
    jQuery.proxy(Model, this)(obj);
    this.absolute_url = '/' + this.name() + '/';
    this.description = ko.observable(obj.description);
    this.url = '/api/groups/' + this.name();
}

var Project = function(obj) {
    jQuery.proxy(Model, this)(obj);
    this.group = obj.group
    this.description = ko.observable(obj.description)
    this.absolute_url = '/' + obj.group + '/' + this.name() + '/';
    this.url = '/api/projects/' + this.name();
}

/*
 *  Generic Collection
 *  
 *  methods:
 *   * fetch: grab all objects for user.
 *   * extractData: pull the data from the api call and create
 *                  this.model objects with the data.
 */
var Collection = function() {
    // Fetching objects for the collection
    this.working = ko.observable(false);
    this.items = ko.observableArray([]);
    this.options = {};
    this.url = '';
    this.model = null;
    
    // Callback for when a item is deleted    
    this.itemDeleted = function(item) {
        this.items.remove(item);
    };
    
    // Callback for new object creation form data
    this.newOptions = function () {
        return {};
    };
    
    // Extract data and enrich it with model object
    this.extractData = function(data) {
        if (data.objects) {
            if (this.model) {
                var objs = data.objects;
                ko.utils.arrayForEach(objs, jQuery.proxy(function(obj) {
                    jQuery.extend(obj, new this.model(obj));
                    obj.onDelete = jQuery.proxy(this.itemDeleted, this);
                }, this));
                return data.objects;
            }
            return data.objects;
        }
        return [];
    };
    
    
    this.addObject = function(formElement) {
        this.working(true);

        jQuery.ajax({
            url : this.url,
            type : 'POST',
            data : this.newOptions(),
            success : $.proxy(function(data) {
                if(data.errorMsg) {
                    this.errors(data.errorMsg);
                } else {
                    var obj = new this.model(data);
                    obj.onDelete = jQuery.proxy(this.itemDeleted, this);
                    this.items.push(obj);
                    this.resetForm();
                }
            }, this),
            error : $.proxy(function(data) {
                console.log(data);
                this.errors(data);
            }, this),
            complete : $.proxy(function() {
                this.working(false);
            }, this)
        });
    };
    
    // Grab list of objects
    this.fetch = function() {
        this.working(true);

        jQuery.ajax({
            url : this.url,
            type : 'GET',
            dataType : 'json',
            data : this.options,
            success : $.proxy(function(data) {
                var newItems = this.extractData(data) || [];
                var items = this.items();
                $.merge(items, newItems);
                this.items(items);
            }, this),
            complete : $.proxy(function() {
                this.working(false);
            }, this)
        });
    };
    
}

var GroupCollection = function() {
    jQuery.proxy(Collection, this)();
    this.url = '/api/groups/';
    this.newName = ko.observable('');
    this.newDescription = ko.observable('');
    this.errors = ko.observable();
    this.formVisible = ko.observable(false);
    this.model = Group;
    
    this.newOptions = function () {
        return {
            name: this.newName(),
            description: this.newDescription(),    
        };
    };

    this.resetForm = function() {
        this.newName('');
        this.newDescription('');
        this.formVisible(false);
        this.errors('');
    };

    this.toggleForm = function() {
        this.formVisible(!this.formVisible());
    };
    
    // Grab the initial groups
    this.fetch();
    
};

var ProjectCollection = function(groupName) {
    jQuery.proxy(Collection, this)();
    this.url = '/api/projects/';
    this.options = {group: groupName};
    this.newName = ko.observable('');
    this.newDescription = ko.observable('');
    this.errors = ko.observable();
    this.formVisible = ko.observable(false);
    this.model = Project;
    
    this.newOptions = function () {
        return {
            name: this.newName(),
            description: this.newDescription(),
            group: groupName,
        };
    };
    
    this.resetForm = function() {
        this.newName('');
        this.newDescription('');
        this.formVisible(false);
        this.errors('');
    };

    this.toggleForm = function() {
        this.formVisible(!this.formVisible());
    };
    
    // Grab the initial groups
    this.fetch();
    
};

// Here's a custom Knockout binding that makes elements shown/hidden via jQuery's fadeIn()/fadeOut() methods
// Could be stored in a separate utility library
ko.bindingHandlers.fadeVisible = {
    init: function(element, valueAccessor) {
        // Initially set the element to be instantly visible/hidden depending on the value
        var value = valueAccessor();
        $(element).toggle(ko.utils.unwrapObservable(value)); // Use "unwrapObservable" so we can handle values that may or may not be observable
    },
    update: function(element, valueAccessor) {
        // Whenever the value subsequently changes, slowly fade the element in or out
        var value = valueAccessor();
        ko.utils.unwrapObservable(value) ? $(element).fadeIn() : $(element).fadeOut();
    }
};

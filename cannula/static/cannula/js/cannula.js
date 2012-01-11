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

    this.resetForm = function() {
        this.newName('');
        this.newDescription('');
        this.formVisible(false);
        this.errors('');
    };

    this.toggleForm = function() {
        this.formVisible(!this.formVisible());
    };

    this.addGroup = function(formElement) {
        this.working(true);

        jQuery.ajax({
            url : this.url,
            type : 'POST',
            data : {
                name : this.newName(),
                description : this.newDescription()
            },
            success : $.proxy(function(data) {
                if(data.errorMsg) {
                    this.errors(data.errorMsg);
                } else {
                    var group = new Group(data);
                    group.onDelete = jQuery.proxy(this.itemDeleted, this);
                    this.items.push(group);
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
    
    // Grab the initial groups
    this.fetch();
    
};

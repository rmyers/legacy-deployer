'use strict';


// Declare app level module which depends on filters, and services
var myApp = angular.module('myApp', ['myApp.filters', 'myApp.services', 'myApp.directives', 'ngCookies','http-auth-interceptor']).
  config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/view1', {templateUrl: 'partials/partial1.html', controller: MyCtrl1});
    $routeProvider.when('/view2', {templateUrl: 'partials/partial2.html', controller: MyCtrl2});
    $routeProvider.when('/people', {templateUrl: 'partials/people.html', controller: PeopleController});
    $routeProvider.otherwise({redirectTo: '/view1'});
  }]);

// Make a reference to httpProvider for use later
myApp.config(['$httpProvider', function($httpProvider) {
  myApp.$httpProvider = $httpProvider;
}]);

// Add a default header for the Django csrftoken
myApp.run(['$cookies', function($cookies){
  myApp.$httpProvider.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
}]);

'use strict';

/* Controllers */


function MyCtrl1() {}
MyCtrl1.$inject = [];


function MyCtrl2() {
}
MyCtrl2.$inject = [];

function PeopleController($resource, $scope, People) {
    People.query({}, function(data){
        $scope.users = data.objects;
        $scope.count = data.meta.total_count;
    });
};

function LoginController($scope, $http, authService) {
	$scope.submit = function () {
		$http.post('../accounts/login/', 
		    'username='+$scope.username+'&password='+$scope.password).
		    success(function() {
				authService.loginConfirmed();
				$scope.username = '';
				$scope.password = '';
				$scope.error = false;
			}).
			error(function(resp) {
				$scope.error = resp.message;
			});
	};
};

PeopleController.$inject = ['$resource', '$scope', 'People'];
LoginController.$inject = ['$scope', '$http', 'authService']

'use strict';

/* Directives */


angular.module('myApp.directives', []).
  directive('whenScrolled', function() {
    return function(scope, elm, attr) {
        var raw = elm[0];
        
        elm.bind('scroll', function() {
            if (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
                scope.$apply(attr.whenScrolled);
            }
        });
    };
  }).
  directive('loginForm', function() {
  	return {
	  	restrict: 'C',
	  	link: function(scope, elm, attr) {
	  	var el = $(elm[0]);
	  	scope.$on('event:auth-loginRequired', function() {
	  	  el.modal('show');
	  	});
	    scope.$on('event:auth-loginConfirmed', function() {
	 	  el.modal('hide');
	  	});
  	  }
  	}
  });
'use strict';

/* Filters */

angular.module('myApp.filters', []).
  filter('interpolate', ['version', function(version) {
    return function(text) {
      return String(text).replace(/\%VERSION\%/mg, version);
    }
  }]);

'use strict';

/* Services */


// Demonstrate how to register services
// In this case it is a simple value service.
angular.module('myApp.services', ['ngResource']).
  factory('People', function($resource) {
      return $resource('../api/v1/user/:userId', {}, {
        query: {method:'GET', params: {limit: 10}}, isArray:false
      });
  }).
  value('version', '0.1');

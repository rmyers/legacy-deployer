'use strict';

/* Controllers */

function MainCntl($scope, $route, $routeParams, $location) {
  $scope.$route = $route;
  $scope.$location = $location;
  $scope.$routeParams = $routeParams;
};

function MyCtrl1() {}
MyCtrl1.$inject = [];


function SignupController($scope, $http, authService) {
  $scope.page = 'signup';
  $scope.submit = function () {
  	if ($scope.password != $scope.confirm) {
  	  $scope.error = "Passwords do not match!";
  	} else {
		$http.post('/accounts/signup/', jQuery.param($scope.user)).
	      success(function() {
			authService.loginConfirmed();
			$scope.username = '';
			$scope.password = '';
			$scope.error = false;
		  }).
		  error(function(resp) {
		  	console.log(resp);
			$scope.error = resp.message;
			authService.loginConfirmed();
		  });
	    };
  	}
};

function PeopleController($resource, $scope, People) {
    People.query({}, function(data){
        $scope.users = data.objects;
        $scope.count = data.meta.total_count;
    });
};

function LoginController($scope, $http, authService) {
	$scope.submit = function () {
		$http.post('/accounts/login/', 
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

SignupController.$inject = ['$scope', '$http', 'authService']
PeopleController.$inject = ['$resource', '$scope', 'People'];
LoginController.$inject = ['$scope', '$http', 'authService']

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
	console.log($scope);
	$scope.submit = function () {
		console.log($scope);
		$http.post('../accounts/login/', 
		    'username='+$scope.username+'&password='+$scope.password).
		    success(function() {
				authService.loginConfirmed();
				$scope.username = '';
				$scope.password = '';
		});
	};
};

PeopleController.$inject = ['$resource', '$scope', 'People'];
LoginController.$inject = ['$scope', '$http', 'authService']

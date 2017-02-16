
var app = angular.module("app", ["ui-listView", "ui.bootstrap", 'ui.tree', 'ngTagsInput', 'ui.thumbnail', 'geolocation', 'mapboxgl-directive', 'ngEmbed']);
app.run([function () {
    mapboxgl.accessToken = 'pk.eyJ1IjoibmFpbWlrYW4iLCJhIjoiY2lraXJkOXFjMDA0OXdhbTYzNTE0b2NtbiJ9.O64XgZQHNHcV2gwNLN2a0Q';

}]);
app.controller("Consensus", ['$scope', '$http', '$uibModal', 'geolocation', function ($scope, $http, $uibModal, geolocation) {
        $scope.listViewOptions = {};
        $scope.search = {"tags":[{"text":"all"}], "post":""};
        $scope.comments = [{"children":[], "node":"No Comments", "parent":0}];
        $scope.all_comments = {}
        $scope.comments_id;
        $scope.active_post_id;
        $scope.posts = [];
        $scope.trends = [];
        $scope.post_moderate={"moderate":{}};
        $scope.toggle = false;
        $scope.post_click_array = {}
        $scope.city = "unknown";

        $scope.close = function() {
            $scope.$modalInstance.close();
        };
        $scope.open = function() {
           $scope.$modalInstance = $uibModal.open({
                scope: $scope,
                templateUrl: "../static/postSubmit.html",
                size: '',
            });
        };

        $scope.closeComment = function() {
            $scope.$modalComment.close();
        };
        $scope.openComment = function(id, parent_id) {
            console.log(parent_id);
            $scope.comments_id = id;
            $scope.newC["parent"]=parent_id;
            $scope.$modalComment = $uibModal.open({
                scope: $scope,
                templateUrl: "../static/commentSubmit.html",
                size: '',
            });
        };
        $scope.isOpen = function(id){
            return (id in $scope.post_click_array) && $scope.post_click_array[id] == true ;
        };
        $scope.openPost = function(id){
            console.log(id);
            if (id in $scope.post_click_array){
                delete $scope.post_click_array[id];
            }else{
                $scope.post_click_array[id] = true;
            }
        };
        $scope.$watch('search.tags', function(newVal, oldVal){
            $scope.loadPosts();
        }, true);
        $scope.setSearch = function(search) {
            $scope.search.tags=[{"text":search}];
            $scope.loadPosts();
        };
        $scope.vote = function(post, vote){
            var url = "/post/" + post  + "/moderate"
            $scope.post_moderate["moderate"][vote] = true;
            var parameter = JSON.stringify($scope.post_moderate)
            $http.post(url, parameter).then(function onSuccess(response) {
                // Handle success
                var data = response.data;
                var status = response.status;
                var statusText = response.statusText;
                var headers = response.headers;
                var config = response.config;
                console.log(data)
                $scope.loadPosts();
                $scope.post_moderate["moderate"] = {};
            });
        };
        $scope.newP = {"title":"", "link":"http://", "text":"", "tags":""}
        $scope.newPost = function(){
            console.log("fuck");
            var url = "/tag/" + $scope.newP.tags;
            var parameter = JSON.stringify({"toponym": $scope.city, "link":$scope.newP.link, "title": $scope.newP.title, "text":$scope.newP.text});
            $http.post(url, parameter).then(function onSuccess(response) {
                // Handle success
                var data = response.data;
                var status = response.status;
                var statusText = response.statusText;
                var headers = response.headers;
                var config = response.config;
                console.log(data)
                $scope.$modalInstance.close();
                $scope.loadPosts();
            });
        };
        $scope.newC = {"text": "", "parent":"", "tag":""}
        $scope.assignParent = function(parent_id){
            $scope.newC["parent"] = parent_id;
        };
        $scope.newComment = function(){
            console.log("fuck");
            var url = "/post/" + $scope.comments_id;
            var parameter = JSON.stringify({"toponym": $scope.city, "text":$scope.newC.text, "parent":$scope.newC.parent, "tag":$scope.newC.tag});
            console.log(parameter);
            $http.post(url, parameter).then(function onSuccess(response) {
                // Handle success
                var data = response.data;
                var status = response.status;
                var statusText = response.statusText;
                var headers = response.headers;
                var config = response.config;
                console.log(data);
                $scope.closeComment();          
            });
        };
        $scope.loadComments = function(id){
            var url = "/post/" + id;
            console.log(url);
            $http.get(url).then(function onSuccess(response) {
                // Handle success
                if (response.status != 200){
                    $scope.all_comments[id]=[{"children":[], "node":"No Comments", "parent":0}];
                }else {
                    $scope.all_comments[id] = response.data;
                }
                $scope.openPost(id);
                console.log(response.data);
            });
        };
        function sleep (time) {
            return new Promise((resolve) => setTimeout(resolve, time));
        }
        $scope.loadPosts = function(){
            $scope.loadTrends();
            var url = "/tag/" + $scope.search.tags.map(function(elem){
                return elem.text;
            }).join("+");
            console.log(url);
            $http.get(url).then(function onSuccess(response) {
                if (response.status != 200){
                    $scope.posts=[]
                }else {
                    $scope.posts = response.data;
                    $scope.posts.map(function(elem){
                        $scope.all_comments[elem.id] = [{"children":[], "node":"No Comments", "parent":0}];
                        elem["html"] = ""
                        elem["thumb"] = ""
                        if (elem.link.length > 0){
                            $scope.loadThumbnail(elem);
                            sleep(500).then(() => {
    // Do something after the sleep!
                            });
                        }
                    });
                    console.log(response.data);
                }
            })
        };
        $scope.loadTrends = function(){
            console.log("fuck");
            var url = "/tags/trending";
            $http.get(url).then(function onSuccess(response) {
                if (response.status != 200){
                    $scope.trends=[];
                }else {
                    $scope.trends = response.data;
                }
                console.log(response.data);
            });
        };
        $scope.loadThumbnail = function(post){
            params = {"key":"39bac78521a64d5abe719a93c2c3b15f",
                      "url":post["link"]};
            $http({url:"https://api.embedly.com/1/oembed", method:"GET", params: params})
            .then(function onSuccess(response) {
                console.log(response.data)
                post["html"] = response.data.html;
                post["thumb"] = response.data.thumbnail_url;
            });
        };
// Usage!
        function CustomControl (options) {
            this.options = this.options || {};

            mapboxgl.util.extend(this.options, options);
        }
        CustomControl.prototype = new mapboxgl.Evented();
        mapboxgl.util.extend(CustomControl.prototype, {
            options: {
                position: 'bottom-left'
            },

            onAdd: function (map) {
                map.on('load', function () {

                    map.addSource("posters", {
                        type: "geojson",
                        data: '/tag/geo/all',
                        cluster: true,
                        clusterMaxZoom: 14, // Max zoom to cluster points on
                        clusterRadius: 50 // Radius of each cluster when clustering points (defaults to 50)
                    });


                    map.addLayer({
                        "id": "unclustered-points",
                        "type": "symbol",
                        "source": "posters",
                        "filter": ["!has", "point_count"],
                        "layout": {
                            "icon-image": "marker-15"
                        }
                    });
                    // count values. Each range gets a different fill color.
                    var layers = [
                        [150, '#f28cb1'],
                        [20, '#f1f075'],
                        [0, '#51bbd6']
                    ];

                    layers.forEach(function (layer, i) {
                        map.addLayer({
                            "id": "cluster-" + i,
                            "type": "circle",
                            "source": "posters",
                            "paint": {
                                "circle-color": layer[1],
                                "circle-radius": 18
                            },
                            "filter": i === 0 ?
                                [">=", "point_count", layer[0]] :
                                ["all",
                                    [">=", "point_count", layer[0]],
                                    ["<", "point_count", layers[i - 1][0]]]
                        });
                    });

                    // Add a layer for the clusters' count labels
                    map.addLayer({
                        "id": "cluster-count",
                        "type": "symbol",
                        "source": "posters",
                        "layout": {
                            "text-field": "{point_count}",
                            "text-font": [
                                "DIN Offc Pro Medium",
                                "Arial Unicode MS Bold"
                            ],
                            "text-size": 12
                        }
                    });
                });
                var container = document.createElement('div');
                return container;
            }
        });
        $scope.glControls = {
            custom: [
                {
                    constructor: CustomControl,
                    name: 'CustomControl1',
                    options: {
                        position: 'bottom-right'
                    }}
            ]
        };
        function codeLatLng(lat, lng) {
            var latlng = new google.maps.LatLng(lat, lng);
            geocoder = new google.maps.Geocoder();
            geocoder.geocode({'latLng': latlng}, function(results, status) {
              if (status == google.maps.GeocoderStatus.OK) {
                if (results[1]) {
                 //formatted address
                //find country name
                     for (var i=0; i<results[0].address_components.length; i++) {
                    for (var b=0;b<results[0].address_components[i].types.length;b++) {

                    //there are different types that might hold a city admin_area_lvl_1 usually does in come cases looking for sublocality type will be more appropriate
                        if (results[0].address_components[i].types[b] == "administrative_area_level_1") {
                            //this is the object you are looking for
                            city= results[0].address_components[i];
                            break;
                        }
                    }
                }
                //city data
                    $scope.city = city.short_name;
                } else {
                    $scope.city = "unknown";
                }
              } else {
                    $scope.city = "unknown";
              }
            });
        }
        geolocation.getLocation().then(function(data){
            $scope.city = codeLatLng(data.coords.latitude, data.coords.longitude);
            console.log($scope.city)
        });

        $scope.loadPosts();
        //$scope.loadPosts();
        //$scope.newPost();
    }]).controller('PostSubmitCtrl', ['$scope', '$modalInstance',
        function($scope, $modalInstance) {
            $scope.newP = {"title":"", "link":"http://", "text":"", "tags":""}
        }
    ]);
app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{a');
    $interpolateProvider.endSymbol('a}');
}]);

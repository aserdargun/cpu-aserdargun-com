import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from def_routes import route_segments

class Routes(unittest.TestCase):
    def test_wildcards_continue_across_new_paths_without_inventing_branches(self):
        routes,count=route_segments('- signal ( u A ) + ROUTED met1 ( 100 200 ) ( 300 * ) NEW met2 ( * 400 ) ( 500 * ) ;',100)
        self.assertEqual(count,1)
        self.assertEqual(routes,[['signal','met1',1,2,3,2],['signal','met2',3,4,5,4]])

    def test_coordinates_reset_for_each_net(self):
        with self.assertRaises(ValueError):route_segments('- a + ROUTED met1 ( 100 200 ) ( 300 * ) ;\n- b + ROUTED met2 ( * 400 ) ;',100)

    def test_flushpoint_extension_is_not_a_third_dimension(self):
        routes,_=route_segments('- a + ROUTED met1 ( 100 200 0 ) ( * 300 ) ;',100)
        self.assertEqual(routes,[['a','met1',1,2,1,3]])

if __name__=='__main__':unittest.main()

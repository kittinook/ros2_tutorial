# One object seen by the rover's camera.
string kind        # sample | rock | landmark | drill_site | core | meteorite
string id          # unique name of the object, e.g. "sample_3" or "Olympus Rock"
float32 range      # distance from the rover's centre to the object's centre, in metres
float32 bearing    # angle to the object in radians: 0 = straight ahead, + = to the left


(defn dir-exists? [pth]
    (= (os/stat pth :mode) :directory))

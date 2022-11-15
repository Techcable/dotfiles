#!/usr/bin/env janet
(import spork/path)

(def dotfiles-path (path/dirname (dyn *current-file*)))

(print "Dotfiles path: " dotfiles-path)

(defn set-color
  ```
  Emits ANSI color codes to set the terminal color

  Tries to be consistent with click.style
  and fish set_style

  Valid keyword arguments:
  bold - Sets bold color
  underline - Sets underline color
  fg, foreground - Sets the foreground color (implied by deafault)
  bg, background - Sets the background color
  ``` 
  [color &keys flags]
    (def ansi-color-names [
      :black
      :red
      :green
      :yellow
      :blue
      :magenta
      :cyan
      :white
    ])
    (defn check-flag [name]
      (let [res (get flags name)]
        (case res
          true true
          nil false
          false false
          (errorf "Unexpected type %t for flag %s: %q" res name res))))
    (defn check-flags [& names] (some check-flag names))
    # https://talyian.github.io/ansicolors/
    # https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters
    (def parts @[])
    (def foreground
      (match {:fg (check-flags :foreground :fg) :bg (check-flags :background :bg)}
        {:fg true :bg false} true
        {:fg false :bg true} false
        {:fg false :bg false} true # Foreground is default
        (error "Cannot set both foreground and background")))
    # Handle color
    (if (= color :reset)
      (array/push parts 0)
      (do
        (def offset (index-of color ansi-color-names))
        (assert (not (nil? offset)) (errorf "Invalid color: %q" color))
        (array/push parts (+ (if foreground 30 40) offset))))
    # misc attributes
    (when (check-flag :bold) (array/push parts 1))
    (when (check-flag :underline) (array/push parts 4))
    (string "\x1b[" (string/join (map string parts) ";") "m"))

# TODO: Make better than Python version. Macros???
(def Mode {
    :set-color set-color
})

(error "TODO: Not yet implemented")

import { forwardRef, SVGProps } from "react";

export interface LucideProps extends SVGProps<SVGSVGElement> {
  /** Color of the icon. Can be a hex value or a CSS color name */
  color?: string;
  /** Size of the icon in pixels */
  size?: number | string;
  /** Stroke width of the icon */
  strokeWidth?: number | string;
}
export const LilypadIcon = forwardRef<SVGSVGElement, LucideProps>(
  ({ color = "currentColor", size = 24, ...props }, ref) => {
    return (
      <svg
        version='1.0'
        xmlns='http://www.w3.org/2000/svg'
        preserveAspectRatio='xMidYMid meet'
        width='48'
        height='48'
        viewBox='11.99 41.75 282.01 200.3'
      >
        <g
          transform='translate(0.000000,262.000000) scale(0.100000,-0.100000)'
          fill='black'
          stroke='none'
        >
          <path d='M2098 2200 c-45 -8 -60 -20 -110 -87 -22 -31 -46 -53 -57 -53 -10 0 -45 -24 -77 -52 -161 -143 -252 -195 -474 -268 -148 -49 -253 -98 -350 -163 -73 -50 -222 -181 -283 -251 -53 -60 -64 -67 -182 -116 -227 -96 -364 -194 -419 -304 -26 -51 -28 -63 -25 -145 4 -86 5 -92 45 -148 78 -111 224 -205 434 -278 184 -64 315 -92 584 -125 115 -14 529 -14 671 0 61 6 175 22 255 36 356 64 639 193 761 346 57 72 69 105 69 189 0 61 -5 80 -32 131 -80 150 -296 275 -609 354 -76 19 -145 34 -153 34 -9 0 -16 3 -16 8 0 11 97 130 239 290 143 162 181 216 181 255 0 42 -71 111 -159 155 -59 29 -76 43 -82 65 -10 36 -53 93 -82 109 -32 17 -87 25 -129 18z m107 -69 c32 -19 55 -65 39 -81 -8 -8 -115 1 -181 15 -29 7 -29 26 0 53 46 43 82 47 142 13z m-157 -132 c36 -12 51 -39 22 -39 -30 0 -26 -38 5 -46 30 -7 32 -28 5 -71 -27 -46 -84 -62 -134 -38 -48 23 -67 60 -56 109 17 79 80 112 158 85z m237 -21 c192 -55 237 -113 153 -196 -48 -48 -125 -90 -313 -171 -160 -70 -240 -114 -320 -175 -82 -63 -230 -230 -257 -288 -12 -26 -23 -48 -24 -48 -1 0 -35 18 -76 39 -117 63 -172 76 -333 76 -97 0 -147 -4 -163 -13 -36 -21 -16 -32 56 -32 114 -1 254 -18 317 -40 77 -26 160 -82 185 -123 41 -66 12 -143 -70 -185 -41 -21 -55 -23 -145 -19 -92 4 -117 11 -310 77 -230 79 -321 121 -338 158 -23 50 81 189 273 365 147 134 262 201 474 274 136 46 275 111 362 169 28 19 55 34 61 34 5 0 15 -16 21 -35 24 -64 114 -114 179 -99 103 24 159 125 123 219 -6 15 -8 31 -5 35 7 11 63 3 150 -22z m-425 -605 c0 -14 -25 -73 -56 -131 l-56 -104 17 -52 c25 -75 89 -210 121 -251 30 -40 25 -67 -14 -73 -62 -9 -159 83 -227 217 -58 117 -58 141 -1 218 50 66 188 203 205 203 6 0 11 -12 11 -27z m258 -199 c17 -48 29 -91 26 -95 -12 -21 -146 37 -164 70 -8 16 -2 26 41 65 28 25 55 46 59 46 4 0 21 -39 38 -86z m180 1 c246 -62 388 -130 501 -238 60 -59 81 -98 81 -157 0 -158 -266 -330 -650 -419 -342 -80 -884 -93 -1245 -31 -308 54 -555 147 -696 264 -88 72 -109 107 -109 183 0 48 5 68 29 105 41 64 119 123 236 178 147 69 135 69 135 1 0 -58 1 -60 48 -98 71 -59 134 -102 272 -186 139 -85 187 -124 194 -159 2 -12 8 -43 13 -68 14 -78 73 -64 73 18 0 50 21 82 52 82 24 0 70 -23 128 -64 60 -43 77 -48 95 -30 32 32 19 60 -42 90 -32 16 -59 34 -61 41 -2 7 17 14 53 18 49 7 59 11 69 34 6 15 30 44 52 64 23 20 47 51 54 67 7 17 16 30 21 30 5 0 19 -17 32 -37 41 -64 111 -119 210 -167 68 -32 115 -63 161 -106 66 -62 89 -70 109 -38 9 13 1 26 -37 68 -25 29 -45 58 -43 64 6 18 77 11 154 -14 77 -25 103 -20 103 21 0 21 -17 30 -102 54 -32 8 -58 20 -58 25 0 6 27 10 60 10 47 0 64 4 80 20 17 17 18 24 9 41 -10 19 -16 21 -63 14 -75 -11 -226 -5 -264 11 -27 11 -40 27 -67 86 -52 114 -53 123 -13 148 18 11 37 20 41 20 19 0 18 -34 -2 -60 -37 -51 -21 -86 26 -53 14 10 32 23 40 28 20 14 53 -29 53 -69 0 -41 21 -71 44 -63 9 4 16 15 16 26 0 26 10 51 21 51 4 0 26 -18 48 -41 43 -42 61 -44 61 -4 0 13 3 26 8 28 4 3 39 -8 77 -24 85 -34 101 -35 116 -8 15 29 -4 46 -64 58 -57 10 -64 16 -47 36 17 21 2 36 -48 50 -41 12 -82 62 -82 101 0 30 0 30 118 -1z'></path>
          <path d='M1937 1913 c-15 -14 -7 -43 12 -43 24 0 33 13 25 34 -6 16 -25 21 -37 9z'></path>
        </g>
      </svg>
    );
  }
);

LilypadIcon.displayName = "LilypadIcon";
main :: IO ()
main = print answer

limit :: Int
limit = 50

points :: [(Int, Int)]
points = [(x, y) | x <- [0..limit], y <- [0..limit], (x, y) /= (0, 0)]

isRightTriangle :: (Int, Int) -> (Int, Int) -> Bool
isRightTriangle p@(x1, y1) q@(x2, y2) =
  p < q && (dotOP == 0 || dotOQ == 0 || dotPQ == 0)
  where
    dotOP = x1 * x2 + y1 * y2
    dotOQ = x2 * (x1 - x2) + y2 * (y1 - y2)
    dotPQ = x1 * (x2 - x1) + y1 * (y2 - y1)

answer :: Int
answer = length [() | p <- points, q <- points, isRightTriangle p q]

/******************************************************************************
This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
*******************************************************************************/

#include <cassert>
#include <tacos/topology/kite.h>
#include <iostream>
#include <vector>
#include <sstream>
#include <string>

using namespace tacos;

Kite::Kite(const int width,
           const int height,
           const Latency latency,
           const Bandwidth bandwidth) noexcept
           : width(width),
             height(height) {
    assert(width > 0);
    assert(height > 0);
    assert(latency >= 0);
    assert(bandwidth > 0);

    // compute NPUs count
    int nodes = width * height;
    setNpusCount(width * height);

    connect(0, 1, latency, bandwidth, false);
    connect(0, 4, latency, bandwidth, false);
    connect(0, 5, latency, bandwidth, false);

    connect(1, 0, latency, bandwidth, false);
    connect(1, 2, latency, bandwidth, false);
    connect(1, 4, latency, bandwidth, false);
    connect(1, 6, latency, bandwidth, false);

    connect(2, 1, latency, bandwidth, false);
    connect(2, 3, latency, bandwidth, false);
    connect(2, 5, latency, bandwidth, false);
    connect(2, 7, latency, bandwidth, false);

    connect(3, 2, latency, bandwidth, false);
    connect(3, 6, latency, bandwidth, false);
    connect(3, 7, latency, bandwidth, false);

    connect(4, 0, latency, bandwidth, false);
    connect(4, 1, latency, bandwidth, false);
    connect(4, 8, latency, bandwidth, false);
    connect(4, 9, latency, bandwidth, false);

    connect(5, 0, latency, bandwidth, false);
    connect(5, 2, latency, bandwidth, false);
    connect(5, 8, latency, bandwidth, false);
    connect(5, 10, latency, bandwidth, false);

    connect(6, 1, latency, bandwidth, false);
    connect(6, 3, latency, bandwidth, false);
    connect(6, 9, latency, bandwidth, false);
    connect(6, 11, latency, bandwidth, false);

    connect(7, 2, latency, bandwidth, false);
    connect(7, 3, latency, bandwidth, false);
    connect(7, 10, latency, bandwidth, false);
    connect(7, 11, latency, bandwidth, false);

    connect(8, 4, latency, bandwidth, false);
    connect(8, 5, latency, bandwidth, false);
    connect(8, 12, latency, bandwidth, false);
    connect(8, 13, latency, bandwidth, false);

    connect(9, 4, latency, bandwidth, false);
    connect(9, 6, latency, bandwidth, false);
    connect(9, 12, latency, bandwidth, false);
    connect(9, 14, latency, bandwidth, false);

    connect(10, 5, latency, bandwidth, false);
    connect(10, 7, latency, bandwidth, false);
    connect(10, 13, latency, bandwidth, false);
    connect(10, 15, latency, bandwidth, false);

    connect(11, 6, latency, bandwidth, false);
    connect(11, 7, latency, bandwidth, false);
    connect(11, 14, latency, bandwidth, false);
    connect(11, 15, latency, bandwidth, false);

    connect(12, 8, latency, bandwidth, false);
    connect(12, 9, latency, bandwidth, false);
    connect(12, 13, latency, bandwidth, false);

    connect(13, 8, latency, bandwidth, false);
    connect(13, 10, latency, bandwidth, false);
    connect(13, 12, latency, bandwidth, false);
    connect(13, 14, latency, bandwidth, false);

    connect(14, 9, latency, bandwidth, false);
    connect(14, 11, latency, bandwidth, false);
    connect(14, 13, latency, bandwidth, false);
    connect(14, 15, latency, bandwidth, false);

    connect(15, 10, latency, bandwidth, false);
    connect(15, 11, latency, bandwidth, false);
    connect(15, 14, latency, bandwidth, false);

    for (auto h = 0; h < height; h++){
        for (auto w = 0; w < width - 1; w++){
            const auto src = (h * width) + w;
            const auto dest = src + 1;
            std::cout << getLatency(src, dest) << " ";
        }
        std::cout << std::endl;
    }
}

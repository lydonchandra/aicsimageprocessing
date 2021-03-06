# Author: Evan Wiederspan <evanw@alleninstitute.org>
import unittest
import numpy as np
from itertools import permutations
from aicsimageprocessing.alignMajor import (
    align_major,
    get_align_angles,
    get_major_minor_axis,
    angle_between,
)


class TestAlignMajor(unittest.TestCase):
    def setUp(self):
        # binary CZYX image with major along x, minor along z
        self.testCube = np.zeros((3, 10, 10, 10))
        self.testCube[:, 5, 5, :] = 1
        self.testCube[:, 5, 0:5, 5] = 1
        self.testCube[:, 6, 5, 5] = 1

    def getRandAxes(self):
        """
        Helper function to get random arrangement of 'xyz'
        """
        return "".join(np.random.permutation(["x", "y", "z"]).tolist())

    def test_angleBetween(self):
        self.assertEqual(
            angle_between(np.array([0, 1]), np.array([0, 1])), 0, "0 degree check"
        )
        self.assertEqual(
            angle_between(np.array([0, 1]), np.array([1, 0])), 90, "90 degree check"
        )
        with self.assertRaises(ValueError, msg="Must take 1d numpy arrays as input"):
            angle_between(np.ones((2, 2)), np.ones((2, 2)))

    def test_getMajorMinorAxis(self):
        # binary CZYX image with major along x axis
        test = np.zeros((3, 10, 10, 10))
        test[:, 5, 5, :] = 1
        # major axis should be parallel to x axis
        major, minor = get_major_minor_axis(test)
        self.assertTrue(
            angle_between(major, np.array([1, 0, 0])) < 1, msg="Major Axis Pre-rotation"
        )

    def test_alignMajorInputs(self):
        with self.assertRaises(ValueError, msg="img must be 4d numpy array"):
            align_major([[1]], "xyz")
        with self.assertRaises(ValueError, msg="axis must be arrangement of 'xyz'"):
            align_major(self.testCube, "aaa")

    def test_alignMajorAlignment(self):
        a_map = {"x": 0, "y": 1, "z": 2}
        # try every alignment possibility
        for axes in list("".join(p) for p in permutations("xyz")):
            angles = get_align_angles(self.testCube, axes)
            res = align_major(self.testCube, angles)
            major, minor = get_major_minor_axis(res)
            self.assertTrue(
                np.argmax(np.abs(major)) == a_map[axes[0]],
                "Major aligned correctly rotating to " + axes,
            )
            self.assertTrue(
                np.argmax(np.abs(minor)) == a_map[axes[-1]],
                "Minor aligned correctly rotating to " + axes,
            )

    def test_alignMajorReshape(self):
        axes = self.getRandAxes()
        angles = get_align_angles(self.testCube, axes)
        res = align_major(self.testCube, angles, False)
        self.assertEqual(
            self.testCube.shape,
            res.shape,
            "Shape stays constant when not reshaping with axes " + axes,
        )

    def test_alignMajorMultiple(self):
        axes = self.getRandAxes()
        angles = get_align_angles(self.testCube, axes)
        res = align_major([self.testCube, self.testCube], angles)
        self.assertTrue(len(res) == 2, "Output same number of images as passed in")
        self.assertTrue(
            np.array_equal(res[0], res[1]), "Multiple images rotated by same amount"
        )

    def test_getAnglesNDim(self):
        axes = self.getRandAxes()
        test3d = np.mean(self.testCube, axis=0)
        test4d = self.testCube
        test5d = np.expand_dims(self.testCube, axis=0)
        self.assertEqual(
            get_align_angles(test3d, axes),
            get_align_angles(test4d, axes),
            "Angles for 3d image equal 4d",
        )
        self.assertEqual(
            get_align_angles(test4d, axes),
            get_align_angles(test5d, axes),
            "Angles for 4d image equal 5d",
        )

    def test_alignMajorNDim(self):
        axes = self.getRandAxes()
        # create a 3d, 4d, and 5d test image
        # rotate them all and compare the last 3 dimensions for each
        # They should all be the same
        test3d = np.mean(self.testCube, axis=0)
        test4d = self.testCube
        test5d = np.expand_dims(self.testCube, axis=0)
        angles = get_align_angles(test5d, axes)
        align_major([test3d, test4d, test5d], angles)
        self.assertTrue(
            np.array_equal(test3d, test4d[0]), "3d equals 4d image after rotate"
        )
        self.assertTrue(
            np.array_equal(test4d[0], test5d[0, 0]), "4d equals 5d image after rotate"
        )
